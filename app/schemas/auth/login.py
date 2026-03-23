from typing import Optional
from pydantic import BaseModel
from ..shared.team import TeamReadBasic

class LoginRequest(BaseModel):
    email: str
    password: str
    access_token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    id: int
    email: str
    full_name: str
    role: str
    expires_at: str
    team: Optional[TeamReadBasic] = None

    class Config:
        from_attributes = True

class MeResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    resume_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    profile_image: Optional[str] = None
    has_profile_image: bool = False
    has_face_embedding: bool = False
    team: Optional[TeamReadBasic] = None

    class Config:
        from_attributes = True
