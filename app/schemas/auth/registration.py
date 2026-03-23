from typing import Optional
from pydantic import BaseModel
from ..shared.user import UserRole

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "candidate"
    team_id: Optional[int] = None
