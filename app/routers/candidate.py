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

from ..schemas.requests import JoinRoomRequest
from ..schemas.responses import HistoryItem, JoinRoomResponse

@router.post("/join", response_model=JoinRoomResponse)
async def join_room(
    request: JoinRoomRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # 1. Find the room
    statement = select(InterviewRoom).where(InterviewRoom.room_code == request.room_code)
    room = session.exec(statement).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    if room.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid room password")
        
    if not room.is_active:
        raise HTTPException(status_code=400, detail="Room is no longer active")
        
    # 2. Check if session already exists for this room/user? 
    # For now, allow multiple sessions or maybe just one? Let's create a new session.
    
    # Check max sessions limit (Only count ACTIVE sessions)
    if room.max_sessions is not None:
        active_sessions_count = len([s for s in room.sessions if s.end_time is None])
        if active_sessions_count >= room.max_sessions:
             raise HTTPException(status_code=400, detail="Room has reached maximum active session limit. Please try again later.")

    try:
        new_session = InterviewSession(
            room_id=room.id,
            candidate_id=current_user.id,
            start_time=datetime.utcnow()
        )
        session.add(new_session)
        session.flush() # Get ID, do not commit
        session.refresh(new_session)
        
        # 3. Assign random questions from the bank (The Campaign Logic)
        if room.bank_id and room.question_count > 0:
            bank_questions = room.bank.questions
            if bank_questions:
                # Pick N random questions
                sample_size = min(len(bank_questions), room.question_count)
                selected = random.sample(bank_questions, sample_size)
                
                for i, q in enumerate(selected):
                    sq = SessionQuestion(
                        session_id=new_session.id,
                        question_id=q.id,
                        sort_order=i
                    )
                    session.add(sq)
        
        # ACID: Single atomic commit for Session + Questions
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to join room: {str(e)}")
    
    return {
        "session_id": new_session.id,
        "room_code": room.room_code,
        "message": "Successfully joined room"
    }

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
        room = session.get(InterviewRoom, s.room_id)
        history.append({
            "session_id": s.id,
            "room_code": room.room_code if room else "N/A",
            "date": s.start_time.strftime("%Y-%m-%d %H:%M"),
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
