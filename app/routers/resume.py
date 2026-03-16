import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/resume", tags=["Resume Management"])

RESUME_DIR = os.path.join("app", "assets", "resumes")

@router.get("/")
async def get_resume(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieve resume PDF for specified user_id or current user.
    Admins can retrieve any, users only their own.
    """
    target_user_id = user_id if user_id is not None else current_user.id
    
    # Permission check
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.id != target_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this resume")
    
    user = session.get(User, target_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Handle Cloudinary URL (Redirect)
    if user.resume_path.startswith("http"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=user.resume_path)

    # Legacy: Handle Local File Path
    if not os.path.exists(user.resume_path):
        raise HTTPException(status_code=404, detail="Local resume file not found")

    return FileResponse(
        user.resume_path,
        media_type="application/pdf"
    )
