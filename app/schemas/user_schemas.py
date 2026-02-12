"""
User Serialization Schemas and Helpers

Provides clean user serialization excluding sensitive fields.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from ..models.db_models import User, UserRole


class UserPublic(BaseModel):
    """Public user information (excludes sensitive fields)"""
    id: int
    email: str
    full_name: str
    role: str
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True


def serialize_user(user: Optional[User], fallback_name: Optional[str] = None, fallback_role: str = "candidate") -> Dict[str, Any]:
    """
    Serialize a User object to a clean flat dict.
    
    Excludes: password_hash, profile_image_bytes, face_embedding, resume_text
    
    Args:
        user: User model instance or None (if user was deleted)
        fallback_name: Name to use if user is None
        fallback_role: Role to use if user is None
        
    Returns:
        Flat dict with user data, e.g. {"id": 1, "email": "...", "full_name": "...", ...}
    """
    if user is None:
        # User was deleted - return fallback data
        return {
            "id": None,
            "email": "deleted@user.com",
            "full_name": fallback_name or "Deleted User",
            "role": fallback_role,
            "profile_image": None
        }
    
    role_key = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_key,
        "profile_image": user.profile_image
    }


def serialize_user_flat(user: User) -> Dict[str, Any]:
    """
    Serialize a User object to a flat dict (for lists and auth responses).
    
    Args:
        user: User model instance
        
    Returns:
        Flat dict with user data
    """
    role_key = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_key,
        "profile_image": user.profile_image
    }
