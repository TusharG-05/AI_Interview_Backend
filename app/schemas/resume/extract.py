from typing import Optional
from pydantic import BaseModel

class ResumeResponse(BaseModel):
    user_id: int
    resume_url: Optional[str] = None
    transcribed_text: Optional[str] = None
    analysis: Optional[dict] = None

    class Config:
        from_attributes = True
