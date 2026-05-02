from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DbConnectionCreate(BaseModel):
    name: str
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    use_vpn: bool = False
    ovpn_content: Optional[str] = None


class DbConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_vpn: Optional[bool] = None
    ovpn_content: Optional[str] = None


class DbConnectionResponse(BaseModel):
    id: int
    user_id: int
    name: str
    host: str
    port: int
    database: str
    username: str
    use_vpn: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
