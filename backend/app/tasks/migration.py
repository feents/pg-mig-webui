import json
import os
import re
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import redis as redis_client

from app.celery_app import celery_app
from app.crypto import decrypt
from app.database import SessionLocal
from app.models import DbConnection, MigrationJob

DUMPS_DIR = Path("/app/data/dumps")
OVPN_DIR = Path("/run/ovpn")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

_redis = redis_client.from_url(REDIS_URL)


def _publish(job_id: int, progress: float, status: str, log: str, target_kind: str = "db"):
    payload = json.dumps({"progress_pct": progress, "status": status, "log": log, "target_kind": target_kind})
    _redis.publish(f"migration:{job_id}", payload)


def _update_job(db, job: MigrationJob, status: str, progress: float, log: str):
    job.status = status
    job.progress_pct = progress
    if job.log_text:
        job.log_text += f"\n{log}"
    else:
        job.log_text = log
    if status in ("success", "success_with_warnings", "failed"):
        job.finished_at = datetime.utcnow()
    db.commit()
    _publish(job.id, progress, status, log, target_kind=job.target_kind)


_RESTORE_IGNORED_RE = re.compile(r"errors ignored on restore:\s*(\d+)", re.IGNORECASE)
_RESTORE_FATAL_PATTERNS = (
    "could not connect to",
    "FATAL:",
    "connection to server",
    "no password supplied",
    "authentication failed",
    "database \"",  # e.g. database "x" does not exist
    "input file appears",
    "out of memory",
)


def _parse_restore_outcome(out: str) -> tuple[int | None, list[str]]:
    """Parse pg_restore output. Returns (ignored_count, failed_toc_entries).
    ignored_count is None if the standard 'errors ignored on restore' summary is absent.
    failed_toc_entries lists the 'from TOC entry ...' lines for context.
    """
    ignored: int | None = None
    m = _RESTORE_IGNORED_RE.search(out)
    if m:
        try:
            ignored = int(m.group(1))
        except ValueError:
            ignored = None
    failed = [line.strip() for line in out.splitlines() if "from TOC entry" in line]
    return ignored, failed


def _restore_has_fatal(out: str) -> bool:
    lowered = out.lower()
    return any(p.lower() in lowered for p in _RESTORE_FATAL_PATTERNS)


def _run(cmd: list[str], env: dict | None = None) -> tuple[int, str]:
    merged_env = {**os.environ, **(env or {})}
    result = subprocess.run(cmd, capture_output=True, text=True, env=merged_env)
    return result.returncode, result.stdout + result.stderr


def _run_streamed(
    cmd: list[str],
    job_id: int,
    progress: float,
    status: str,
    env: dict | None = None,
    timeout: int = 21600,
    target_kind: str = "db",
) -> tuple[int, str]:
    """stderr를 Redis로 실시간 스트리밍하며 명령어 실행. timeout 초 초과 시 프로세스 강제 종료."""
    merged_env = {**os.environ, **(env or {})}
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        env=merged_env,
    )
    lines: list[str] = []

    def _reader():
        for line in proc.stderr:
            stripped = line.rstrip()
            if stripped:
                lines.append(stripped)
                _publish(job_id, progress, status, stripped, target_kind=target_kind)

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        proc.kill()
        proc.wait()
        lines.append(f"타임아웃({timeout}초) 초과로 프로세스 강제 종료")
        return -1, "\n".join(lines)

    proc.wait()
    return proc.returncode, "\n".join(lines)


def _wait_for_vpn_ready(log_path: Path, timeout: int = 60) -> bool:
    for _ in range(timeout):
        if log_path.exists():
            try:
                if "Initialization Sequence Completed" in log_path.read_text(errors="ignore"):
                    return True
            except OSError:
                pass
        time.sleep(1)
    return False


def _start_vpn(ovpn_content: str, target_host: str, job_id: int, prefix: str) -> tuple[subprocess.Popen, Path, Path, Path]:
    OVPN_DIR.mkdir(parents=True, exist_ok=True)
    ovpn_path = OVPN_DIR / f"vpn_{prefix}_{job_id}.ovpn"
    log_path = OVPN_DIR / f"vpn_{prefix}_{job_id}.log"
    pid_path = OVPN_DIR / f"vpn_{prefix}_{job_id}.pid"

    # 서버가 DB 호스트 라우트를 push하지 않을 수 있어, 클라이언트 측에서 강제로 추가
    # verb 5로 raise해서 route 처리 로그를 확실히 남김
    augmented = ovpn_content.rstrip() + f"\nverb 5\nroute {target_host} 255.255.255.255\n"
    ovpn_path.write_text(augmented)
    proc = subprocess.Popen(
        ["openvpn", "--daemon",
         "--log", str(log_path),
         "--writepid", str(pid_path),
         "--config", str(ovpn_path)],
    )
    return proc, ovpn_path, log_path, pid_path


def _stop_vpn(vpn_proc: subprocess.Popen | None, ovpn_path: Path, log_path: Path, pid_path: Path):
    try:
        if pid_path.exists():
            pid = int(pid_path.read_text().strip())
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass
    if vpn_proc:
        try:
            vpn_proc.terminate()
        except Exception:
            pass
    for p in [ovpn_path, log_path, pid_path]:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass


@celery_app.task
def run_migration(job_id: int):
    DUMPS_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    src_vpn_proc: subprocess.Popen | None = None
    src_ovpn_path: Path = OVPN_DIR / f"vpn_src_{job_id}.ovpn"
    src_log_path: Path = OVPN_DIR / f"vpn_src_{job_id}.log"
    src_pid_path: Path = OVPN_DIR / f"vpn_src_{job_id}.pid"
    tgt_vpn_proc: subprocess.Popen | None = None
    tgt_ovpn_path: Path = OVPN_DIR / f"vpn_tgt_{job_id}.ovpn"
    tgt_log_path: Path = OVPN_DIR / f"vpn_tgt_{job_id}.log"
    tgt_pid_path: Path = OVPN_DIR / f"vpn_tgt_{job_id}.pid"

    try:
        job = db.query(MigrationJob).filter(MigrationJob.id == job_id).first()
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        _publish(job_id, 0, "running", "이관 작업 시작")

        src_kind = job.source_kind
        tgt_kind = job.target_kind
        has_warnings = False

        # 소스 처리
        if src_kind == "db":
            src = db.query(DbConnection).filter(DbConnection.id == job.source_conn_id).first()
            src_password = decrypt(src.password_enc)
            dump_path = DUMPS_DIR / f"dump_{job_id}.pgdump"

            # 소스 VPN 연결
            if src.use_vpn and src.ovpn_content_enc:
                _update_job(db, job, "running", 5, f"소스 OpenVPN 연결 중... (host route: {src.host})")
                src_vpn_proc, src_ovpn_path, src_log_path, src_pid_path = _start_vpn(decrypt(src.ovpn_content_enc), src.host, job_id, "src")
                if not _wait_for_vpn_ready(src_log_path):
                    vpn_log = src_log_path.read_text(errors="ignore") if src_log_path.exists() else "(로그 없음)"
                    raise RuntimeError(f"소스 OpenVPN 연결 타임아웃 (60초)\n{vpn_log}")
                _update_job(db, job, "running", 10, "소스 OpenVPN 연결 완료")

            _update_job(db, job, "running", 10, "pg_dump 시작...")
            rc, out = _run_streamed(
                [
                    "pg_dump", "-Fc", "-v",
                    "--exclude-table-data=public.spatial_ref_sys",
                    "-h", src.host, "-p", str(src.port),
                    "-U", src.username, "-d", src.database,
                    "-f", str(dump_path),
                ],
                job_id=job_id,
                progress=20,
                status="running",
                env={"PGPASSWORD": src_password},
                target_kind=tgt_kind,
            )
            if rc != 0:
                vpn_log = src_log_path.read_text(errors="ignore") if src_vpn_proc and src_log_path.exists() else ""
                raise RuntimeError(f"pg_dump 실패:\n{out}" + (f"\n\n[VPN 로그]\n{vpn_log}" if vpn_log else ""))
            _update_job(db, job, "running", 30, f"pg_dump 완료: {dump_path.name}")

            # 소스 VPN 종료 (대상 VPN과 tun 충돌 방지)
            if src_vpn_proc:
                _stop_vpn(src_vpn_proc, src_ovpn_path, src_log_path, src_pid_path)
                src_vpn_proc = None

        else:  # src_kind == "file"
            dump_path = Path(job.source_file_path)
            if not dump_path.exists():
                raise RuntimeError(f"업로드된 파일을 찾을 수 없습니다: {dump_path}")
            _update_job(db, job, "running", 30, f"업로드 파일 사용: {dump_path.name}")

        # 대상 처리
        if tgt_kind == "db":
            tgt = db.query(DbConnection).filter(DbConnection.id == job.target_conn_id).first()
            tgt_password = decrypt(tgt.password_enc)

            # 대상 VPN 연결
            if tgt.use_vpn and tgt.ovpn_content_enc:
                _update_job(db, job, "running", 40, "대상 OpenVPN 연결 중...")
                tgt_vpn_proc, tgt_ovpn_path, tgt_log_path, tgt_pid_path = _start_vpn(decrypt(tgt.ovpn_content_enc), tgt.host, job_id, "tgt")
                if not _wait_for_vpn_ready(tgt_log_path):
                    vpn_log = tgt_log_path.read_text(errors="ignore") if tgt_log_path.exists() else "(로그 없음)"
                    raise RuntimeError(f"대상 OpenVPN 연결 타임아웃 (60초)\n{vpn_log}")
                _update_job(db, job, "running", 50, "대상 OpenVPN 연결 완료")

            # pg_restore
            _update_job(db, job, "running", 60, "pg_restore 시작...")
            rc, out = _run_streamed(
                [
                    "pg_restore", "-v", "-j", "4",
                    "--no-owner", "--no-privileges",
                    "-h", tgt.host, "-p", str(tgt.port),
                    "-U", tgt.username, "-d", tgt.database,
                    str(dump_path),
                ],
                job_id=job_id,
                progress=70,
                status="running",
                env={"PGPASSWORD": tgt_password},
                target_kind=tgt_kind,
            )
            ignored_count, failed_toc = _parse_restore_outcome(out)
            partial_ok = rc != 0 and ignored_count is not None and not _restore_has_fatal(out)
            if rc != 0 and not partial_ok:
                raise RuntimeError(f"pg_restore 실패:\n{out}")
            if partial_ok:
                _update_job(
                    db, job, "running", 80,
                    f"pg_restore 부분 완료: 무시된 오류 {ignored_count}건 "
                    f"(주로 확장(extension) 버전 불일치로 인한 MATERIALIZED VIEW REFRESH 실패 등).",
                )
                if failed_toc:
                    _update_job(db, job, "running", 80, "실패 항목:")
                    for entry in failed_toc[:10]:
                        _update_job(db, job, "running", 80, f"  - {entry}")
                    if len(failed_toc) > 10:
                        _update_job(db, job, "running", 80, f"  ... 외 {len(failed_toc) - 10}건")
                has_warnings = True
            else:
                _update_job(db, job, "running", 80, "pg_restore 완료")

        else:  # tgt_kind == "file"
            job.target_file_path = str(dump_path)
            db.commit()
            _update_job(db, job, "running", 80, f"덤프 파일 준비 완료: {dump_path.name}")

        final_status = "success_with_warnings" if has_warnings else "success"
        final_log = "이관 완료 (경고 포함)" if has_warnings else "이관 완료"
        _update_job(db, job, final_status, 100, final_log)

    except Exception as exc:
        try:
            _update_job(db, job, "failed", job.progress_pct, f"오류: {exc}")
        except Exception:
            pass

    finally:
        # VPN 종료
        _stop_vpn(src_vpn_proc, src_ovpn_path, src_log_path, src_pid_path)
        _stop_vpn(tgt_vpn_proc, tgt_ovpn_path, tgt_log_path, tgt_pid_path)

        # 덤프 파일: 파일 다운로드 대상이면 보존, 아니면 삭제
        try:
            if job.target_kind != "file":
                Path(DUMPS_DIR / f"dump_{job_id}.pgdump").unlink(missing_ok=True)
        except Exception:
            pass

        # 업로드된 소스 파일 삭제
        try:
            if job.source_kind == "file" and job.source_file_path:
                Path(job.source_file_path).unlink(missing_ok=True)
        except Exception:
            pass

        db.close()
