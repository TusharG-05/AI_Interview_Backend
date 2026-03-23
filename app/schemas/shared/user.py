from typing import Optional
from pydantic import BaseModel
from .team import TeamReadBasic

class UserNested(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    access_token: Optional[str] = None
    profile_image: Optional[str] = None
    profile_image_url: Optional[str] = None
    team: Optional[TeamReadBasic] = None

    class Config:
        from_attributes = True

class LoginUserNested(UserNested):
    """Specific for login response if needed, otherwise same as UserNested."""
    pass
