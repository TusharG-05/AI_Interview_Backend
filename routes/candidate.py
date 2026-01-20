from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from config.database import get_session
from models.db_models import User, InterviewRoom, InterviewSession, InterviewResponse
from auth.dependencies import get_current_user
from pydantic import BaseModel
from datetime import datetime

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/candidate", tags=["Candidate"])

@router.get("/dashboard", response_class=HTMLResponse)
async def candidate_dashboard(request: Request):
    return templates.TemplateResponse("dashboard_candidate.html", {"request": request})

class JoinRoomRequest(BaseModel):
    room_code: str
    password: str

class JoinRoomResponse(BaseModel):
    session_id: int
    room_code: str
    message: str

class HistoryItem(BaseModel):
    session_id: int
    room_code: str
    date: str
    score: float = None

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
