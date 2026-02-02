from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import Question, InterviewRoom, InterviewSession, InterviewResponse, User, UserRole, ProctoringEvent
from ..auth.dependencies import get_admin_user
from ..auth.security import get_password_hash
from ..services.nlp import NLPService
from ..schemas.requests import RoomCreate, RoomUpdate, QuestionCreate, UserCreate
from ..schemas.responses import RoomRead, SessionRead, UserRead, DetailedResult, ResponseDetail, ProctoringLogItem, InterviewLinkResponse
import os
import shutil
import uuid
import secrets
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])
nlp_service = NLPService()

# --- Question Management ---

@router.get("/questions", response_model=List[Question])
async def get_questions(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all available interview questions."""
    return session.exec(select(Question)).all()

@router.post("/questions", response_model=Question)
async def add_question(
    q_data: QuestionCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """API for manually adding a new interview question."""
    new_q = Question(
        content=q_data.content,
        question_text=q_data.content,
        topic=q_data.topic,
        difficulty=q_data.difficulty,
        reference_answer=q_data.reference_answer
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

@router.delete("/questions/{q_id}")
async def delete_question(
    q_id: int, 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    q = session.get(Question, q_id)
    if not q: raise HTTPException(status_code=404, detail="Question not found")
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
    room_code = secrets.token_hex(3).upper()
    while session.exec(select(InterviewRoom).where(InterviewRoom.room_code == room_code)).first():
        room_code = secrets.token_hex(3).upper()
        
    new_room = InterviewRoom(
        room_code=room_code,
        password=room_data.password,
        admin_id=current_user.id,
        max_sessions=room_data.max_sessions or 30
    )
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    return RoomRead(id=new_room.id, room_code=new_room.room_code, password=new_room.password, is_active=new_room.is_active, max_sessions=new_room.max_sessions, active_sessions_count=0)

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

@router.post("/shutdown")
def shutdown(current_user: User = Depends(get_admin_user)):
    if current_user.role != UserRole.SUPER_ADMIN: raise HTTPException(status_code=403)
    os.kill(os.getpid(), 15)
    return {"message": "Shutting down"}
