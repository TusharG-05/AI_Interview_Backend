from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from config.database import get_session
from models.db_models import User, InterviewRoom, InterviewSession, InterviewResponse
from auth.dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/candidate", tags=["Candidate"])

from schemas.requests import JoinRoomRequest
from schemas.responses import HistoryItem, JoinRoomResponse

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

    new_session = InterviewSession(
        room_id=room.id,
        candidate_id=current_user.id,
        start_time=datetime.utcnow()
    )
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    
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
