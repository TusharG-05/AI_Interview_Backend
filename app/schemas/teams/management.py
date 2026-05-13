from typing import List, Optional
from pydantic import BaseModel
from ..shared.user import UserNested

class TeamCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class TeamUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TeamDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    user_count: Optional[int] = 0
    users: List[UserNested] = []

    class Config:
        from_attributes = True
