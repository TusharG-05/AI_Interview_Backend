from typing import Optional
from pydantic import BaseModel

class TabSwitchRequest(BaseModel):
    event_type: str = "TAB_SWITCH"
    is_active: bool = False
    reason: Optional[str] = None


class PingResponse(BaseModel):
    status: str = "ok"
    timestamp: str

class KeepAliveRequest(BaseModel):
    access_token: str
