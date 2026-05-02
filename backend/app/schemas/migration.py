from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MigrationCreate(BaseModel):
    source_kind: str = "db"       # db | file
    target_kind: str = "db"       # db | file
    source_conn_id: Optional[int] = None
    target_conn_id: Optional[int] = None


class MigrationResponse(BaseModel):
    id: int
    user_id: Optional[int]
    source_conn_id: Optional[int]
    target_conn_id: Optional[int]
    source_conn_name: Optional[str]
    target_conn_name: Optional[str]
    source_kind: str
    target_kind: str
    source_file_path: Optional[str]
    target_file_path: Optional[str]
    status: str
    progress_pct: float
    log_text: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}
