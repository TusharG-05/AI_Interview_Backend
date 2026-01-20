from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from config.database import get_session
from models.db_models import User, InterviewRoom, InterviewSession, InterviewResponse
from auth.dependencies import get_admin_user
from pydantic import BaseModel
import secrets

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("dashboard_admin.html", {"request": request})

class RoomCreate(BaseModel):
    password: str

class RoomRead(BaseModel):
    id: int
    room_code: str
    is_active: bool

class SessionRead(BaseModel):
    id: int
    candidate_name: str
    room_code: str
    start_time: str
    total_score: float = None

@router.post("/rooms", response_model=RoomRead)
async def create_room(
    room_data: RoomCreate, 
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    # Generate unique room code
    room_code = secrets.token_hex(3).upper()
    while session.exec(select(InterviewRoom).where(InterviewRoom.room_code == room_code)).first():
        room_code = secrets.token_hex(3).upper()
        
    new_room = InterviewRoom(
        room_code=room_code,
        password=room_data.password,
        admin_id=current_user.id
    )
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    return new_room

@router.get("/rooms", response_model=List[RoomRead])
async def list_rooms(
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    # List rooms created by this admin
    statement = select(InterviewRoom).where(InterviewRoom.admin_id == current_user.id)
    rooms = session.exec(statement).all()
    return rooms

@router.get("/history", response_model=List[SessionRead])
async def get_all_interview_history(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    # Get all finished sessions
    statement = select(InterviewSession).where(InterviewSession.end_time != None).order_by(InterviewSession.start_time.desc())
    sessions = session.exec(statement).all()
    
    result = []
    for s in sessions:
        candidate = session.get(User, s.candidate_id)
        room = session.get(InterviewRoom, s.room_id)
        result.append({
            "id": s.id,
            "candidate_name": candidate.full_name if candidate else "Unknown",
            "room_code": room.room_code if room else "N/A",
            "start_time": s.start_time.isoformat(),
            "total_score": s.total_score
        })
    return result
