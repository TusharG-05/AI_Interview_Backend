from typing import Optional
from pydantic import BaseModel

class VideoStatusResponse(BaseModel):
    status: str
    recording_url: Optional[str] = None
    last_event: Optional[str] = None
    timestamp: str

    class Config:
        from_attributes = True
