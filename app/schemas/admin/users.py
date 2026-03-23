from typing import List, Optional
from pydantic import BaseModel
from ..shared.user import UserNested
from ..shared.team import TeamReadBasic

class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    resume_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    team: Optional[TeamReadBasic] = None

    class Config:
        from_attributes = True

class GetUserDetailResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    has_profile_image: bool = False
    has_face_embedding: bool = False
    created_interviews_count: int = 0
    participated_interviews_count: int = 0
    resume_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    team: Optional[TeamReadBasic] = None

    class Config:
        from_attributes = True

class CreateUserRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "candidate"
    team_id: Optional[int] = None
