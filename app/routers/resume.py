import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole # Assuming UserRole is defined here or imported
from ..auth.dependencies import get_current_user

from ..schemas.api_response import ApiResponse
from ..schemas.responses import ResumeResponse

router = APIRouter(prefix="/resume", tags=["Resume Management"])

@router.get("/", response_model=ApiResponse[ResumeResponse])
async def get_resume(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieve resume metadata for specified user_id or current user.
    Admins can retrieve any, users only their own.
    Returns the absolute Cloudinary URL in the response body.
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

    # Return the absolute path as requested for all response bodies
    return ApiResponse(
        status_code=200,
        data=ResumeResponse(
            user_id=target_user_id,
            resume_url=user.resume_path
        ),
        message="Resume details retrieved successfully"
    )
