import json
import os
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
    if status in ("success", "failed"):
        job.finished_at = datetime.utcnow()
    db.commit()
    _publish(job.id, progress, status, log, target_kind=job.target_kind)


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


def _wait_for_tun(timeout: int = 30) -> bool:
    for _ in range(timeout):
        rc, out = _run(["ip", "link", "show", "tun0"])
        if rc == 0:
            return True
        time.sleep(1)
    return False


@celery_app.task
def run_migration(job_id: int):
    DUMPS_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    vpn_proc = None
    ovpn_path = OVPN_DIR / f"vpn_{job_id}.ovpn"

    try:
        job = db.query(MigrationJob).filter(MigrationJob.id == job_id).first()
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        _publish(job_id, 0, "running", "이관 작업 시작")

        src_kind = job.source_kind
        tgt_kind = job.target_kind

        # 소스 처리
        if src_kind == "db":
            src = db.query(DbConnection).filter(DbConnection.id == job.source_conn_id).first()
            src_password = decrypt(src.password_enc)
            dump_path = DUMPS_DIR / f"dump_{job_id}.pgdump"

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
                raise RuntimeError(f"pg_dump 실패:\n{out}")
            _update_job(db, job, "running", 30, f"pg_dump 완료: {dump_path.name}")

        else:  # src_kind == "file"
            dump_path = Path(job.source_file_path)
            if not dump_path.exists():
                raise RuntimeError(f"업로드된 파일을 찾을 수 없습니다: {dump_path}")
            _update_job(db, job, "running", 30, f"업로드 파일 사용: {dump_path.name}")

        # 대상 처리
        if tgt_kind == "db":
            tgt = db.query(DbConnection).filter(DbConnection.id == job.target_conn_id).first()
            tgt_password = decrypt(tgt.password_enc)

            # VPN 연결
            if tgt.use_vpn and tgt.ovpn_content_enc:
                _update_job(db, job, "running", 40, "OpenVPN 연결 중...")
                OVPN_DIR.mkdir(parents=True, exist_ok=True)
                ovpn_path.write_text(decrypt(tgt.ovpn_content_enc))
                vpn_proc = subprocess.Popen(
                    ["openvpn", "--daemon",
                     "--log", str(OVPN_DIR / f"vpn_{job_id}.log"),
                     "--config", str(ovpn_path)],
                )
                if not _wait_for_tun():
                    raise RuntimeError("OpenVPN tun 인터페이스 생성 타임아웃 (30초)")
                _update_job(db, job, "running", 50, "OpenVPN 연결 완료")

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
            if rc != 0:
                raise RuntimeError(f"pg_restore 실패:\n{out}")
            _update_job(db, job, "running", 80, "pg_restore 완료")

        else:  # tgt_kind == "file"
            job.target_file_path = str(dump_path)
            db.commit()
            _update_job(db, job, "running", 80, f"덤프 파일 준비 완료: {dump_path.name}")

        _update_job(db, job, "success", 100, "이관 완료")

    except Exception as exc:
        try:
            _update_job(db, job, "failed", job.progress_pct, f"오류: {exc}")
        except Exception:
            pass

    finally:
        # VPN 종료
        if vpn_proc:
            try:
                vpn_proc.terminate()
            except Exception:
                pass
            _run(["pkill", "-f", f"vpn_{job_id}.ovpn"])

        # VPN 임시 파일 삭제
        for p in [ovpn_path, OVPN_DIR / f"vpn_{job_id}.log"]:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass

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
