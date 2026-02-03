from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import Question, QuestionBank, QuestionGroup, InterviewRoom, InterviewSession, InterviewResponse, User, UserRole, ProctoringEvent
from ..auth.dependencies import get_admin_user
from ..auth.security import get_password_hash
from ..services.nlp import NLPService
from ..schemas.requests import RoomCreate, RoomUpdate, QuestionCreate, UserCreate, BankCreate
from ..schemas.responses import RoomRead, SessionRead, UserRead, DetailedResult, ResponseDetail, ProctoringLogItem, InterviewLinkResponse, BankRead
import os
import shutil
import uuid
import secrets
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])
nlp_service = NLPService()

# --- Question Bank & Question Management ---

@router.get("/banks", response_model=List[BankRead])
async def list_banks(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all question banks created by the admin."""
    banks = session.exec(select(QuestionBank).where(QuestionBank.admin_id == current_user.id)).all()
    return [BankRead(
        id=b.id, name=b.name, description=b.description, 
        question_count=len(b.questions), created_at=b.created_at.isoformat()
    ) for b in banks]

@router.post("/banks", response_model=BankRead)
async def create_bank(
    bank_data: BankCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new collection of questions."""
    new_bank = QuestionBank(
        name=bank_data.name,
        description=bank_data.description,
        admin_id=current_user.id
    )
    session.add(new_bank)
    session.commit()
    session.refresh(new_bank)
    return BankRead(id=new_bank.id, name=new_bank.name, description=new_bank.description, question_count=0, created_at=new_bank.created_at.isoformat())

@router.get("/banks/{bank_id}/questions", response_model=List[Question])
async def get_bank_questions(
    bank_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all questions within a specific bank."""
    bank = session.get(QuestionBank, bank_id)
    if not bank or bank.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bank not found")
    return bank.questions

@router.post("/banks/{bank_id}/questions", response_model=Question)
async def add_question_to_bank(
    bank_id: int,
    q_data: QuestionCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """API for manually adding a new interview question to a bank."""
    bank = session.get(QuestionBank, bank_id)
    if not bank or bank.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bank not found")
        
    new_q = QuestionGroup(
        bank_id=bank_id,
        content=q_data.content,
        question_text=q_data.content,
        topic=q_data.topic,
        difficulty=q_data.difficulty,
        reference_answer=q_data.reference_answer,
        marks=q_data.marks
    )
    session.add(new_q)
    session.commit()
    session.refresh(new_q)
    return new_q

@router.post("/upload-doc")
async def upload_document(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Extract Q&A pairs from an uploaded document (Resume/Job Desc)."""
    os.makedirs("temp_uploads", exist_ok=True)
    file_path = f"temp_uploads/{uuid.uuid4().hex[:8]}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        qa_pairs = nlp_service.extract_qa_from_file(file_path)
        for pair in qa_pairs:
            q = Question(content=pair['question'], question_text=pair['question'], reference_answer=pair['answer'], topic="Resume/Document")
            session.add(q)
        session.commit()
        return {"message": f"Successfully extracted {len(qa_pairs)} questions"}
    finally:
        if os.path.exists(file_path): os.remove(file_path)

@router.delete("/banks/{bank_id}")
async def delete_bank(
    bank_id: int, 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a question bank and all its questions."""
    bank = session.get(QuestionBank, bank_id)
    if not bank or bank.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Bank not found")
        
    # Check if any room is using this bank
    room_using = session.exec(select(InterviewRoom).where(InterviewRoom.bank_id == bank_id)).first()
    if room_using:
        raise HTTPException(status_code=400, detail=f"Cannot delete bank. It is currently assigned to room '{room_using.room_code}'.")

    # Delete all questions in this bank first
    questions = session.exec(select(QuestionGroup).where(QuestionGroup.bank_id == bank_id)).all()
    for q in questions:
        session.delete(q)
        
    session.delete(bank)
    session.commit()
    return {"message": "Bank and its questions deleted successfully"}

@router.delete("/questions/{q_id}")
async def delete_question(
    q_id: int, 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    q = session.get(QuestionGroup, q_id)
    if not q: raise HTTPException(status_code=404, detail="Question not found")
    
    # Verify ownership via bank (Question -> Bank -> Admin)
    # Questions might be legacy or linked to a bank.
    if q.bank:
        if q.bank.admin_id != current_user.id:
             raise HTTPException(status_code=403, detail="Not authorized to delete this question")
             
    session.delete(q)
    session.commit()
    return {"message": "Question deleted"}

# --- Room Management ---

@router.post("/rooms", response_model=RoomRead)
async def create_room(
    room_data: RoomCreate, 
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    # Validate Bank
    bank = session.get(QuestionBank, room_data.bank_id)
    if not bank or bank.admin_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid Question Bank ID")
    
    # Validate Question Count
    if room_data.question_count > len(bank.questions):
        raise HTTPException(
            status_code=400, 
            detail=f"Bank only has {len(bank.questions)} questions. Cannot request {room_data.question_count}."
        )

    room_code = secrets.token_hex(3).upper()
    while session.exec(select(InterviewRoom).where(InterviewRoom.room_code == room_code)).first():
        room_code = secrets.token_hex(3).upper()
        
    new_room = InterviewRoom(
        room_code=room_code,
        password=room_data.password,
        admin_id=current_user.id,
        bank_id=room_data.bank_id,
        question_count=room_data.question_count,
        max_sessions=room_data.max_sessions or 30,
        interviewer_id=room_data.interviewer_id
    )
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    return RoomRead(id=new_room.id, room_code=new_room.room_code, password=new_room.password, is_active=new_room.is_active, max_sessions=new_room.max_sessions, active_sessions_count=0)


@router.patch("/rooms/{room_id}", response_model=RoomRead)
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
    if room_data.interviewer_id is not None:
        # Validate interviewer exists
        interviewer = session.get(User, room_data.interviewer_id)
        if not interviewer: raise HTTPException(status_code=400, detail="Interviewer not found")
        room.interviewer_id = room_data.interviewer_id
        
    session.add(room)
    session.commit()
    session.refresh(room)
    return RoomRead(id=room.id, room_code=room.room_code, password=room.password, is_active=room.is_active, max_sessions=room.max_sessions, active_sessions_count=len([s for s in room.sessions if s.end_time is None]))

@router.get("/rooms", response_model=List[RoomRead])
async def list_rooms(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    rooms = session.exec(select(InterviewRoom).where(InterviewRoom.admin_id == current_user.id)).all()
    return [RoomRead(id=r.id, room_code=r.room_code, password=r.password, is_active=r.is_active, max_sessions=r.max_sessions, active_sessions_count=len([s for s in r.sessions if s.end_time is None])) for r in rooms]


# --- Results & Proctoring ---

@router.get("/users/results", response_model=List[DetailedResult])
async def get_all_results(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """API for the admin dashboard: Returns all candidate details and their interview results/audit logs."""
    rooms = session.exec(select(InterviewRoom).where(InterviewRoom.admin_id == current_user.id)).all()
    room_ids = [r.id for r in rooms]
    sessions = session.exec(select(InterviewSession).where(InterviewSession.room_id.in_(room_ids))).all()
    
    results = []
    for s in sessions:
        responses = s.responses
        proctoring = s.proctoring_events
        
        avg_score = sum([r.score for r in responses if r.score is not None]) / len(responses) if responses else 0
        
        results.append(DetailedResult(
            session_id=s.id,
            candidate=s.candidate.full_name if s.candidate else (s.candidate_name or "Unknown"),
            date=s.start_time.strftime("%Y-%m-%d %H:%M"),
            score=f"{round(avg_score * 100, 1)}%",
            flags=len(proctoring) > 0,
            details=[ResponseDetail(
                question=r.question.question_text or r.question.content or "Dynamic",
                answer=r.answer_text or r.transcribed_text or "[No Answer]",
                score=f"{round(r.score * 100, 1) if r.score is not None else 0}%"
            ) for r in responses],
            proctoring_logs=[ProctoringLogItem(
                type=e.event_type,
                time=e.timestamp.strftime("%H:%M:%S"),
                details=e.details
            ) for e in proctoring]
        ))
    return results

# --- Identity & System ---

@router.post("/upload-identity")
async def upload_identity(file: UploadFile = File(...), current_user: User = Depends(get_admin_user)):
    content = await file.read()
    from ..services.camera import CameraService
    if CameraService().update_identity(content): return {"message": "Identity updated"}
    raise HTTPException(status_code=500, detail="Failed to update identity")

@router.post("/users", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new user (Candidate or Admin)."""
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return UserRead(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value
    )

@router.get("/users", response_model=List[UserRead])
async def list_users(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    return [UserRead(id=u.id, email=u.email, full_name=u.full_name, role=u.role.value) for u in session.exec(select(User)).all()]

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int, 
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    """Delete a user. Handles dependencies based on role."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete super admin")

    # Handle dependencies based on role
    
    # 1. If user is ADMIN or INTERVIEWER/ADMIN (role=admin)
    # Check if they own any question banks or rooms
    # We choose to BLOCK delete if they own core assets, forcing manual cleanup or reassignment.
    
    owned_banks = session.exec(select(QuestionBank).where(QuestionBank.admin_id == user.id)).first()
    if owned_banks:
         raise HTTPException(status_code=400, detail=f"Cannot delete user. They own Question Banks (e.g. ID {owned_banks.id}). Delete or reassign banks first.")

    created_rooms = session.exec(select(InterviewRoom).where(InterviewRoom.admin_id == user.id)).first()
    if created_rooms:
         raise HTTPException(status_code=400, detail=f"Cannot delete user. They created Rooms (e.g. {created_rooms.room_code}). Delete rooms first.")

    # 2. If user is INTERVIEWER (or assigned as one)
    # Reassign rooms they are *assigned* to back to None
    assigned_rooms = session.exec(select(InterviewRoom).where(InterviewRoom.interviewer_id == user.id)).all()
    for room in assigned_rooms:
        room.interviewer_id = None
        session.add(room)
        
    # 3. If user is CANDIDATE
    # Delete their sessions & responses?
    # Usually we might want to keep history, but "Delete User" implies GDPR-style wipe.
    # So we cascade delete sessions.
    
    sessions = session.exec(select(InterviewSession).where(InterviewSession.candidate_id == user.id)).all()
    for s in sessions:
        # Cascade delete responses usually handled by DB, but manual cleanup is safer if not set up
        # Responses rely on session_id, so deleting session should be enough if DB enforced.
        # But let's check Proctoring/Responses just in case.
        # Given we are not 100% sure of SQLite cascade setup, let's just delete the user and let SQLite/ORM handle or fail.
        # But strictly speaking, we should delete children.
        # Let's trust ORM/SQLite foreign key cascade if it was set, 
        # BUT our Models (db_models.py) don't explicitly say `cascade="all, delete"`.
        # So manual cleanup is safer.
        for r in s.responses: session.delete(r)
        for e in s.proctoring_events: session.delete(e)
        session.delete(s)

    session.delete(user)
    session.commit()
    return {"message": f"User {user.email} deleted successfully"}

@router.post("/shutdown")
def shutdown(current_user: User = Depends(get_admin_user)):
    if current_user.role != UserRole.SUPER_ADMIN: raise HTTPException(status_code=403)
    os.kill(os.getpid(), 15)
    return {"message": "Shutting down"}
