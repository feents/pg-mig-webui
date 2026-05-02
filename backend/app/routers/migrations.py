import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import DbConnection, MigrationJob, User
from app.schemas.migration import MigrationCreate, MigrationResponse
from app.tasks.migration import run_migration

router = APIRouter(prefix="/api/migrations", tags=["migrations"])

UPLOADS_DIR = Path("/app/data/uploads")
DUMPS_DIR = Path("/app/data/dumps")


def _user_conn_ids(db: Session, user_id: int) -> list[int]:
    return [c.id for c in db.query(DbConnection).filter(DbConnection.user_id == user_id).all()]


def _owns_job(db: Session, job_id: int, user: User) -> MigrationJob:
    conn_ids = _user_conn_ids(db, user.id)
    job = db.query(MigrationJob).filter(
        MigrationJob.id == job_id,
        or_(
            MigrationJob.user_id == user.id,
            and_(MigrationJob.source_conn_id.isnot(None),
                 MigrationJob.source_conn_id.in_(conn_ids)),
        ),
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="migrations.not_found")
    return job


@router.post("", response_model=MigrationResponse, status_code=status.HTTP_201_CREATED)
def create_migration(
    body: MigrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    src = tgt = None
    if body.source_kind == "db":
        if not body.source_conn_id:
            raise HTTPException(status_code=400, detail="migrations.source_conn_required")
        src = db.query(DbConnection).filter(
            DbConnection.id == body.source_conn_id, DbConnection.user_id == current_user.id
        ).first()
        if not src:
            raise HTTPException(status_code=404, detail="migrations.source_not_found")

    if body.target_kind == "db":
        if not body.target_conn_id:
            raise HTTPException(status_code=400, detail="migrations.target_conn_required")
        tgt = db.query(DbConnection).filter(
            DbConnection.id == body.target_conn_id, DbConnection.user_id == current_user.id
        ).first()
        if not tgt:
            raise HTTPException(status_code=404, detail="migrations.target_not_found")

    if src and tgt and src.id == tgt.id:
        raise HTTPException(status_code=400, detail="migrations.same_source_target")

    job = MigrationJob(
        user_id=current_user.id,
        source_kind=body.source_kind,
        target_kind=body.target_kind,
        source_conn_id=body.source_conn_id,
        target_conn_id=body.target_conn_id,
        source_conn_name=src.name if src else None,
        target_conn_name=tgt.name if tgt else None,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_migration.delay(job.id)
    return job


@router.post("/from-file", response_model=MigrationResponse, status_code=status.HTTP_201_CREATED)
async def create_migration_from_file(
    target_conn_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tgt = db.query(DbConnection).filter(
        DbConnection.id == target_conn_id, DbConnection.user_id == current_user.id
    ).first()
    if not tgt:
        raise HTTPException(status_code=404, detail="migrations.target_not_found")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4()}.pgdump"
    file_path = UPLOADS_DIR / file_name

    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    job = MigrationJob(
        user_id=current_user.id,
        source_kind="file",
        target_kind="db",
        source_conn_id=None,
        target_conn_id=target_conn_id,
        source_conn_name=None,
        target_conn_name=tgt.name,
        source_file_path=str(file_path),
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_migration.delay(job.id)
    return job


@router.get("/{job_id}/download")
def download_dump(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _owns_job(db, job_id, current_user)
    if job.target_kind != "file":
        raise HTTPException(status_code=400, detail="migrations.not_file_target")
    if job.status != "success":
        raise HTTPException(status_code=400, detail="migrations.not_completed")
    if not job.target_file_path or not Path(job.target_file_path).exists():
        raise HTTPException(status_code=404, detail="migrations.dump_not_found")
    return FileResponse(
        path=job.target_file_path,
        filename=f"migration_{job_id}.pgdump",
        media_type="application/octet-stream",
    )


@router.get("", response_model=List[MigrationResponse])
def list_migrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conn_ids = _user_conn_ids(db, current_user.id)
    return (
        db.query(MigrationJob)
        .filter(
            or_(
                MigrationJob.user_id == current_user.id,
                and_(
                    MigrationJob.source_conn_id.isnot(None),
                    MigrationJob.source_conn_id.in_(conn_ids),
                ),
            )
        )
        .order_by(MigrationJob.id.desc())
        .all()
    )


@router.get("/{job_id}", response_model=MigrationResponse)
def get_migration(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _owns_job(db, job_id, current_user)
