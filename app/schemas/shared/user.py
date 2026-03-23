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

from typing import Dict, Any
from ...models.db_models import User, UserRole

def serialize_user(user: Optional[User], fallback_name: Optional[str] = None, fallback_role: str = "candidate") -> Dict[str, Any]:
    if user is None:
        return {
            "id": None,
            "email": "deleted@user.com",
            "full_name": fallback_name or "Deleted User",
            "role": fallback_role,
            "profile_image": None,
            "profile_image_url": None,
            "resume_url": None,
            "team": None
        }
    
    role_key = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    team_data = None
    if hasattr(user, "team") and user.team:
        team_data = {
            "id": user.team.id,
            "name": user.team.name,
            "description": user.team.description,
            "created_at": user.team.created_at.isoformat() if user.team.created_at else ""
        }

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_key,
        "profile_image": user.profile_image,
        "profile_image_url": f"/api/candidate/profile-image/{user.id}" if user.profile_image_bytes or hasattr(user, 'profile_image') and user.profile_image else None,
        "resume_url": getattr(user, 'resume_path', None),
        "team": team_data
    }

def serialize_user_flat(user: User) -> Dict[str, Any]:
    role_key = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    team_data = None
    if hasattr(user, "team") and user.team:
         team_data = {
            "id": user.team.id,
            "name": user.team.name,
            "description": user.team.description,
            "created_at": user.team.created_at.isoformat() if user.team.created_at else ""
        }

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_key,
        "profile_image": user.profile_image,
        "profile_image_url": f"/api/candidate/profile-image/{user.id}" if user.profile_image_bytes or user.profile_image else None,
        "resume_url": getattr(user, 'resume_path', None),
        "team": team_data
    }
