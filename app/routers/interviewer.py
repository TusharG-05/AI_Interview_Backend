from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime

from ..core.database import get_db as get_session
from ..models.db_models import User, InterviewRoom, InterviewSession, QuestionBank, ProctoringEvent, UserRole
from ..auth.dependencies import get_interviewer_user
from ..schemas.responses import RoomRead, BankRead
from ..schemas.requests import BankCreate, JoinRoomRequest

router = APIRouter(prefix="/interviewer", tags=["Interviewer"])

# --- Room Management ---

@router.get("/rooms", response_model=List[RoomRead])
async def list_assigned_rooms(
    current_user: User = Depends(get_interviewer_user), 
    session: Session = Depends(get_session)
):
    """List rooms assigned to the current interviewer (or all if Admin)."""
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        # Admins see all rooms (or just their own? Prompt says Admin can act as interviewer)
        # Let's show rooms assigned to them AND rooms they created.
        # But specifically "/interviewer/rooms" usually implies "rooms I am responsible for interviewing".
        # Let's show rooms where they are interviewer OR admin.
        statement = select(InterviewRoom).where(
            (InterviewRoom.interviewer_id == current_user.id) | 
            (InterviewRoom.admin_id == current_user.id)
        )
    else:
        statement = select(InterviewRoom).where(InterviewRoom.interviewer_id == current_user.id)
        
    rooms = session.exec(statement).all()
    return [RoomRead(
        id=r.id, 
        room_code=r.room_code, 
        password=r.password, 
        is_active=r.is_active, 
        max_sessions=r.max_sessions, 
        active_sessions_count=len([s for s in r.sessions if s.end_time is None])
    ) for r in rooms]

@router.get("/rooms/{room_id}", response_model=RoomRead)
async def get_room_details(
    room_id: int,
    current_user: User = Depends(get_interviewer_user),
    session: Session = Depends(get_session)
):
    room = session.get(InterviewRoom, room_id)
    if not room: raise HTTPException(status_code=404, detail="Room not found")
    
    # Access check
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if room.interviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized for this room")
            
    return RoomRead(
        id=room.id, 
        room_code=room.room_code, 
        password=room.password, 
        is_active=room.is_active, 
        max_sessions=room.max_sessions, 
        active_sessions_count=len([s for s in room.sessions if s.end_time is None])
    )

@router.post("/rooms/{room_id}/candidates")
async def invite_candidate(
    room_id: int,
    current_user: User = Depends(get_interviewer_user),
    session: Session = Depends(get_session)
):
    """Generates an invitation link (mocked) for the room."""
    # Re-use get logic to ensure access
    await get_room_details(room_id, current_user, session)
    
    room = session.get(InterviewRoom, room_id)
    # In a real app, send email. Here return the info.
    return {
        "message": "Invite candidate using these credentials",
        "room_code": room.room_code,
        "password": room.password,
        "invite_link": f"/candidate/join?code={room.room_code}"
    }

@router.post("/rooms/{room_id}/attach-bank/{bank_id}")
async def attach_question_bank(
    room_id: int,
    bank_id: int,
    current_user: User = Depends(get_interviewer_user),
    session: Session = Depends(get_session)
):
    # Check room access
    room = session.get(InterviewRoom, room_id)
    if not room: raise HTTPException(status_code=404, detail="Room not found")
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if room.interviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized for this room")

    # Check bank access (Interviewer can use their own banks)
    bank = session.get(QuestionBank, bank_id)
    if not bank: raise HTTPException(status_code=404, detail="Bank not found")
    
    # Simplicity: Allow attaching ANY bank they created, OR if they are admin.
    # If they are just interviewer, they should own the bank.
    if current_user.role == UserRole.INTERVIEWER and bank.admin_id != current_user.id:
         raise HTTPException(status_code=403, detail="Cannot attach a bank you do not own")
         
    room.bank_id = bank_id
    session.add(room)
    session.commit()
    return {"message": f"Bank '{bank.name}' attached to room '{room.room_code}'"}

# --- Session Management ---

@router.post("/sessions/{session_id}/kick")
async def kick_candidate(
    session_id: int,
    current_user: User = Depends(get_interviewer_user),
    session: Session = Depends(get_session)
):
    interview_session = session.get(InterviewSession, session_id)
    if not interview_session: raise HTTPException(status_code=404, detail="Session not found")
    
    room = interview_session.room
    if not room: raise HTTPException(status_code=404, detail="Room associated with session not found")

    # Access check
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if room.interviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to manage this session")

    if interview_session.is_completed:
        return {"message": "Session already completed"}

    # Kick logic
    interview_session.is_completed = True
    interview_session.end_time = datetime.utcnow()
    session.add(interview_session)
    
    # Log event
    event = ProctoringEvent(
        session_id=session_id,
        event_type="KICKED",
        details=f"Candidate kicked by {current_user.role.value} ({current_user.email})",
        timestamp=datetime.utcnow()
    )
    session.add(event)
    
    session.commit()
    return {"message": "Candidate kicked successfully", "session_id": session_id}

# --- Question Bank Management (Interviewer Specific) ---

@router.post("/banks", response_model=BankRead)
async def create_interviewer_bank(
    bank_data: BankCreate,
    current_user: User = Depends(get_interviewer_user),
    session: Session = Depends(get_session)
):
    """Interviewer creates their own question bank."""
    new_bank = QuestionBank(
        name=bank_data.name,
        description=bank_data.description,
        admin_id=current_user.id # Assigned to creator
    )
    session.add(new_bank)
    session.commit()
    session.refresh(new_bank)
    return BankRead(
        id=new_bank.id, 
        name=new_bank.name, 
        description=new_bank.description, 
        question_count=0, 
        created_at=new_bank.created_at.isoformat()
    )
