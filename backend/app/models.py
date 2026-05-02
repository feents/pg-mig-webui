from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user")      # admin | user
    status: Mapped[str] = mapped_column(String, default="pending") # active | pending
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    connections: Mapped[list["DbConnection"]] = relationship(back_populates="owner")


class DbConnection(Base):
    __tablename__ = "db_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=5432)
    database: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    password_enc: Mapped[str] = mapped_column(Text, nullable=False)
    use_vpn: Mapped[bool] = mapped_column(Boolean, default=False)
    ovpn_content_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="connections")


class MigrationJob(Base):
    __tablename__ = "migration_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    source_conn_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("db_connections.id"), nullable=True)
    target_conn_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("db_connections.id"), nullable=True)
    source_kind: Mapped[str] = mapped_column(String, default="db")   # db | file
    target_kind: Mapped[str] = mapped_column(String, default="db")   # db | file
    source_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_conn_name: Mapped[str | None] = mapped_column(String, nullable=True)
    target_conn_name: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")   # pending|running|success|failed
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    log_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
