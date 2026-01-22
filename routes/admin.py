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

from schemas.requests import RoomCreate, RoomUpdate
from schemas.responses import RoomRead, SessionRead

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
        admin_id=current_user.id,
        max_sessions=room_data.max_sessions
    )
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    return RoomRead(
        id=new_room.id,
        room_code=new_room.room_code,
        is_active=new_room.is_active,
        max_sessions=new_room.max_sessions,
        active_sessions_count=0
    )

@router.put("/rooms/{room_id}", response_model=RoomRead)
async def update_room(
    room_id: int,
    room_data: RoomUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    room = session.get(InterviewRoom, room_id)
    if not room or room.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room_data.password is not None:
        room.password = room_data.password
    if room_data.max_sessions is not None:
        room.max_sessions = room_data.max_sessions
    if room_data.is_active is not None:
        room.is_active = room_data.is_active
        
    session.add(room)
    session.commit()
    session.refresh(room)
    
    # helper for active count
    active_count = len(room.sessions)
    
    return RoomRead(
        id=room.id,
        room_code=room.room_code,
        is_active=room.is_active,
        max_sessions=room.max_sessions,
        active_sessions_count=active_count
    )

@router.delete("/rooms/{room_id}")
async def delete_room(
    room_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    room = session.get(InterviewRoom, room_id)
    if not room or room.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Room not found")
        
    session.delete(room)
    session.commit()
    return {"message": "Room deleted successfully"}

@router.get("/rooms", response_model=List[RoomRead])
async def list_rooms(
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    # List rooms created by this admin
    statement = select(InterviewRoom).where(InterviewRoom.admin_id == current_user.id)
    rooms = session.exec(statement).all()
    
    result = []
    for r in rooms:
        result.append(RoomRead(
            id=r.id,
            room_code=r.room_code,
            is_active=r.is_active,
            max_sessions=r.max_sessions,
            active_sessions_count=len(r.sessions)
        ))
    return result

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
