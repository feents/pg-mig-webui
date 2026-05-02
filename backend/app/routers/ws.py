import asyncio
import json
import os

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

router = APIRouter(tags=["websocket"])

JWT_SECRET = os.getenv("JWT_SECRET", "")
ALGORITHM = "HS256"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


@router.websocket("/ws/migrations/{job_id}")
async def migration_ws(websocket: WebSocket, job_id: int, token: str = ""):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    r = aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()

    # 구독 먼저 — 이후 DB 조회와 라이브 메시지 사이의 유실 방지
    await pubsub.subscribe(f"migration:{job_id}")

    # 기존 로그 재생 (DB에서 조회)
    from app.database import SessionLocal
    from app.models import MigrationJob

    def _get_job():
        db = SessionLocal()
        try:
            return db.query(MigrationJob).filter(MigrationJob.id == job_id).first()
        finally:
            db.close()

    job = await asyncio.to_thread(_get_job)
    target_kind = job.target_kind if job else "db"
    if job and job.log_text:
        for line in job.log_text.split("\n"):
            if line.strip():
                await websocket.send_text(json.dumps({
                    "progress_pct": job.progress_pct,
                    "status": job.status,
                    "target_kind": target_kind,
                    "log": line,
                }))

    # 이미 종료된 작업이면 최종 상태 전송 후 닫기
    if job and job.status in ("success", "failed"):
        await websocket.send_text(json.dumps({
            "progress_pct": job.progress_pct,
            "status": job.status,
            "target_kind": target_kind,
            "log": "",
        }))
        await pubsub.unsubscribe(f"migration:{job_id}")
        await r.aclose()
        try:
            await websocket.close()
        except Exception:
            pass
        return

    # 라이브 메시지 스트리밍
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            data = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]
            await websocket.send_text(data)
            parsed = json.loads(data)
            if parsed.get("status") in ("success", "failed"):
                break
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        await pubsub.unsubscribe(f"migration:{job_id}")
        await r.aclose()
        try:
            await websocket.close()
        except Exception:
            pass
