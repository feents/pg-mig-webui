from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import Base, engine
from app.routers import admin, auth, connections, migrations, ws


def _migrate_db():
    """기존 DB에 신규 컬럼 추가 및 nullable 변환."""
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(migration_jobs)")).fetchall()}
        new_cols = {
            "user_id": "INTEGER REFERENCES users(id)",
            "source_kind": "TEXT NOT NULL DEFAULT 'db'",
            "target_kind": "TEXT NOT NULL DEFAULT 'db'",
            "source_file_path": "TEXT",
            "target_file_path": "TEXT",
            "source_conn_name": "TEXT",
            "target_conn_name": "TEXT",
        }
        for col_name, col_def in new_cols.items():
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE migration_jobs ADD COLUMN {col_name} {col_def}"))
                conn.commit()

        # 기존 row 이름 백필: conn_name이 NULL이고 conn_id가 있는 경우 현재 이름으로 채움
        conn.execute(text("""
            UPDATE migration_jobs
            SET source_conn_name = (
                SELECT name FROM db_connections WHERE id = migration_jobs.source_conn_id
            )
            WHERE source_conn_name IS NULL AND source_conn_id IS NOT NULL
        """))
        conn.execute(text("""
            UPDATE migration_jobs
            SET target_conn_name = (
                SELECT name FROM db_connections WHERE id = migration_jobs.target_conn_id
            )
            WHERE target_conn_name IS NULL AND target_conn_id IS NOT NULL
        """))
        conn.commit()

        # source_conn_id / target_conn_id를 nullable로 변환 (필요 시 테이블 재생성)
        cols_info = {row[1]: row for row in conn.execute(text("PRAGMA table_info(migration_jobs)")).fetchall()}
        src_col = cols_info.get("source_conn_id")
        if src_col and src_col[3] == 1:   # notnull=1
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migration_jobs_new (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    source_conn_id INTEGER REFERENCES db_connections(id),
                    target_conn_id INTEGER REFERENCES db_connections(id),
                    source_kind TEXT NOT NULL DEFAULT 'db',
                    target_kind TEXT NOT NULL DEFAULT 'db',
                    source_file_path TEXT,
                    target_file_path TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress_pct REAL NOT NULL DEFAULT 0.0,
                    log_text TEXT,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP
                )
            """))
            conn.execute(text("""
                INSERT OR IGNORE INTO migration_jobs_new
                    (id, user_id, source_conn_id, target_conn_id,
                     source_kind, target_kind, source_file_path, target_file_path,
                     status, progress_pct, log_text, started_at, finished_at)
                SELECT id, user_id, source_conn_id, target_conn_id,
                       COALESCE(source_kind, 'db'), COALESCE(target_kind, 'db'),
                       source_file_path, target_file_path,
                       status, progress_pct, log_text, started_at, finished_at
                FROM migration_jobs
            """))
            conn.execute(text("DROP TABLE migration_jobs"))
            conn.execute(text("ALTER TABLE migration_jobs_new RENAME TO migration_jobs"))
            conn.commit()


Base.metadata.create_all(bind=engine)
_migrate_db()

app = FastAPI(title="pg-mig-webui")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(connections.router)
app.include_router(migrations.router)
app.include_router(ws.router)


@app.get("/health")
def health():
    return {"status": "ok"}
