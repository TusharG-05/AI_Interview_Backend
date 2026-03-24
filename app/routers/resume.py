 
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole
from ..auth.dependencies import get_current_user

from ..schemas.shared.api_response import ApiResponse
from ..schemas.resume.extract import ResumeResponse

router = APIRouter(prefix="/resume", tags=["Resume Management"])
from ..auth.dependencies import get_current_user_optional
from ..models.db_models import InterviewSession

@router.get("/", response_model=ApiResponse[ResumeResponse])
async def get_resume(
    user_id: Optional[int] = None,
    interview_token: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    """
    Retrieve resume metadata for specified user_id or current user.
    Admins can retrieve any, users only their own.
    Allows access via interview_token for candidates.
    """
    # 1. Resolve target_user_id
    target_user_id = user_id
    
    if interview_token:
        # Validate token and get candidate_id
        interview = session.exec(select(InterviewSession).where(InterviewSession.access_token == interview_token)).first()
        if not interview:
            raise HTTPException(status_code=401, detail="Invalid interview token")
        if target_user_id is not None and target_user_id != interview.candidate_id:
            raise HTTPException(status_code=403, detail="Token mismatch for user_id")
        target_user_id = interview.candidate_id
        # Token access granted!
    elif current_user:
        if target_user_id is None:
            target_user_id = current_user.id
            
        # Permission check for logged-in user
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.id != target_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this resume")
    else:
        raise HTTPException(status_code=401, detail="Authentication required (Token or Login)")
    
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