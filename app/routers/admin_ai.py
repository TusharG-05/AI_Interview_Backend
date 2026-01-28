from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User, InterviewRoom, InterviewSession, InterviewResponse, UserRole
from ..auth.dependencies import get_admin_user
from ..auth.security import get_password_hash
from pydantic import BaseModel
import secrets
from ..schemas.requests import RoomCreate, RoomUpdate, AdminCreate, UserUpdate
from ..schemas.responses import RoomRead, SessionRead, UserRead

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("dashboard_admin.html", {"request": request})

@router.post("/rooms", response_model=RoomRead)
async def create_room(
    room_data: RoomCreate, 
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    # Validate max_sessions
    if room_data.max_sessions is not None and room_data.max_sessions <= 0:
        raise HTTPException(status_code=400, detail="Max sessions must be a positive number")

    # Generate unique room code
    room_code = secrets.token_hex(3).upper()
    while session.exec(select(InterviewRoom).where(InterviewRoom.room_code == room_code)).first():
        room_code = secrets.token_hex(3).upper()
        
    new_room = InterviewRoom(
        room_code=room_code,
        password=room_data.password,
        admin_id=current_user.id,
        max_sessions=room_data.max_sessions if room_data.max_sessions is not None else 30
    )
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    return RoomRead(
        id=new_room.id,
        room_code=new_room.room_code,
        password=new_room.password,
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
        if room_data.max_sessions <= 0:
            raise HTTPException(status_code=400, detail="Max sessions must be a positive number")
        room.max_sessions = room_data.max_sessions
    if room_data.is_active is not None:
        room.is_active = room_data.is_active
        
    session.add(room)
    session.commit()
    session.refresh(room)
    
    
    # helper for active count
    active_count = len([s for s in room.sessions if s.end_time is None])
    
    return RoomRead(
        id=room.id,
        room_code=room.room_code,
        password=room.password,
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
        
    # Manual Cascade Delete: Responses -> Sessions -> Room
    # 1. Get all sessions for this room
    sessions = session.exec(select(InterviewSession).where(InterviewSession.room_id == room_id)).all()
    
    for s in sessions:
        # 2. Delete responses for each session
        statement = select(InterviewResponse).where(InterviewResponse.session_id == s.id)
        responses = session.exec(statement).all()
        for r in responses:
            session.delete(r)
        
        # 3. Delete the session itself
        session.delete(s)
        
    # 4. Delete the room
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
            password=r.password,
            is_active=r.is_active,
            max_sessions=r.max_sessions,
            active_sessions_count=len([s for s in r.sessions if s.end_time is None])
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

# --- User Management Endpoints ---

@router.post("/users", response_model=UserRead)
async def create_admin(
    user_data: AdminCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    # Only Super Admin can create other admins
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin can create admins")
        
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user_data.password)
    new_admin = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hashed_password,
        role=UserRole.ADMIN
    )
    session.add(new_admin)
    session.commit()
    session.refresh(new_admin)
    
    return UserRead(
        id=new_admin.id, 
        email=new_admin.email, 
        full_name=new_admin.full_name, 
        role=new_admin.role.value
    )

@router.get("/users", response_model=List[UserRead])
async def list_users(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    users = session.exec(select(User)).all()
    return [
        UserRead(id=u.id, email=u.email, full_name=u.full_name, role=u.role.value)
        for u in users
    ]

@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    user_to_edit = session.get(User, user_id)
    if not user_to_edit:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Permission Logic
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super Admin can edit anyone
        pass
    else:
        # Ordinary Admin
        if user_to_edit.role != UserRole.CANDIDATE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins can only edit candidates")
            
    if user_data.email is not None:
        # Check uniqueness if email changes
        if user_data.email != user_to_edit.email:
             existing = session.exec(select(User).where(User.email == user_data.email)).first()
             if existing:
                 raise HTTPException(status_code=400, detail="Email already registered")
        user_to_edit.email = user_data.email
        
    if user_data.full_name is not None:
        user_to_edit.full_name = user_data.full_name
        
    if user_data.password is not None and user_data.password.strip():
        user_to_edit.password_hash = get_password_hash(user_data.password)
        
    session.add(user_to_edit)
    session.commit()
    session.refresh(user_to_edit)
    
    return UserRead(
        id=user_to_edit.id, 
        email=user_to_edit.email, 
        full_name=user_to_edit.full_name, 
        role=user_to_edit.role.value
    )
