from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import psycopg2

from app.auth import get_current_user
from app.crypto import decrypt, encrypt
from app.database import get_db
from app.models import DbConnection, User
from app.schemas.connection import DbConnectionCreate, DbConnectionResponse, DbConnectionTest, DbConnectionUpdate

router = APIRouter(prefix="/api/connections", tags=["connections"])


def _pg_test(host: str, port: int, database: str, username: str, password: str) -> Dict[str, Any]:
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=database,
            user=username, password=password,
            connect_timeout=5,
        )
        conn.close()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


def _get_owned(conn_id: int, user: User, db: Session) -> DbConnection:
    conn = db.query(DbConnection).filter(DbConnection.id == conn_id, DbConnection.user_id == user.id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="connections.not_found")
    return conn


@router.post("/test")
def test_connection(body: DbConnectionTest, current_user: User = Depends(get_current_user)):
    return _pg_test(body.host, body.port, body.database, body.username, body.password)


@router.post("/{conn_id}/test")
def test_saved_connection(
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = _get_owned(conn_id, current_user, db)
    return _pg_test(conn.host, conn.port, conn.database, conn.username, decrypt(conn.password_enc))


@router.post("", response_model=DbConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(
    body: DbConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = DbConnection(
        user_id=current_user.id,
        name=body.name,
        host=body.host,
        port=body.port,
        database=body.database,
        username=body.username,
        password_enc=encrypt(body.password),
        use_vpn=body.use_vpn,
        ovpn_content_enc=encrypt(body.ovpn_content) if body.use_vpn and body.ovpn_content else None,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.get("", response_model=List[DbConnectionResponse])
def list_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DbConnection).filter(DbConnection.user_id == current_user.id).all()


@router.get("/{conn_id}", response_model=DbConnectionResponse)
def get_connection(conn_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_owned(conn_id, current_user, db)


@router.put("/{conn_id}", response_model=DbConnectionResponse)
def update_connection(
    conn_id: int,
    body: DbConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = _get_owned(conn_id, current_user, db)
    if body.name is not None:
        conn.name = body.name
    if body.host is not None:
        conn.host = body.host
    if body.port is not None:
        conn.port = body.port
    if body.database is not None:
        conn.database = body.database
    if body.username is not None:
        conn.username = body.username
    if body.password is not None:
        conn.password_enc = encrypt(body.password)
    if body.use_vpn is not None:
        conn.use_vpn = body.use_vpn
    if body.ovpn_content is not None:
        conn.ovpn_content_enc = encrypt(body.ovpn_content)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(conn_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conn = _get_owned(conn_id, current_user, db)
    db.delete(conn)
    db.commit()
