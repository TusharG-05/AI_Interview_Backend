from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User, InterviewSession, InterviewResponse, SessionQuestion
from ..auth.dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime
import random

router = APIRouter(prefix="/candidate", tags=["Candidate"])

from ..schemas.responses import HistoryItem, JoinRoomResponse


@router.get("/history", response_model=List[HistoryItem])
async def my_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(InterviewSession).where(
        InterviewSession.candidate_id == current_user.id
    ).order_by(InterviewSession.start_time.desc())
    
    sessions = session.exec(statement).all()
    
    history = []
    for s in sessions:
        history.append({
            "session_id": s.id,
            "room_code": s.access_token[:8] + "...", # Using access token fragment as identifier
            "date": s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "Scheduled",
            "score": s.total_score
        })
    return history

import shutil
import os
from fastapi import UploadFile, File

@router.post("/upload-selfie")
async def upload_selfie(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Allows candidate to upload their reference selfie for face verification."""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    # Create directory
    upload_dir = "app/assets/images/profiles"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file with unique name (but consistent for user to avoid clutter? or history? Let's use user_id)
    # Actually, using user_id allows easy overwrite and retrieval
    file_path = f"{upload_dir}/user_{current_user.id}.jpg"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Update DB
    current_user.profile_image = file_path
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {"message": "Selfie uploaded successfully", "path": file_path}
