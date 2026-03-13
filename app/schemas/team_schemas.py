from typing import Optional
from pydantic import BaseModel

class TeamReadBasic(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    user_count: int = 0

    class Config:
        from_attributes = True
