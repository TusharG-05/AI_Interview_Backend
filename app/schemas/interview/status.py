from typing import Optional
from pydantic import BaseModel

class TabSwitchRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None

class PingResponse(BaseModel):
    status: str = "ok"
    timestamp: str

class KeepAliveRequest(BaseModel):
    access_token: str
