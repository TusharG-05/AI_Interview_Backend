from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import QuestionBank, QuestionGroup, InterviewSession, InterviewResponse, User, UserRole, ProctoringEvent, InterviewStatus
from ..auth.dependencies import get_admin_user
from ..auth.security import get_password_hash
from ..services.nlp import NLPService
from ..services.email import EmailService
from ..schemas.requests import QuestionCreate, UserCreate, InterviewScheduleCreate
from ..schemas.responses import BankRead, SessionRead, UserRead, DetailedResult, ResponseDetail, ProctoringLogItem, InterviewLinkResponse
import os
import shutil
import uuid
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])
nlp_service = NLPService()
email_service = EmailService()

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

class BankCreate(BaseModel):
    name: str
    description: Optional[str] = None

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

@router.get("/banks/{bank_id}/questions", response_model=List[QuestionGroup])
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

@router.post("/banks/{bank_id}/questions", response_model=QuestionGroup)
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
    # 1. Validation (DoS Prevention)
    if not file.filename.lower().endswith(('.pdf', '.txt', '.docx')):
         raise HTTPException(status_code=400, detail="Only PDF, TXT, or DOCX files are allowed.")
    
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    MAX_SIZE = 10 * 1024 * 1024 # 10MB
    if size > MAX_SIZE:
         raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_SIZE/1024/1024}MB.")

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

# --- Interview Scheduling ---

@router.post("/interviews/schedule", response_model=InterviewLinkResponse)
async def schedule_interview(
    schedule_data: InterviewScheduleCreate, 
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    """
    Schedule a new one-to-one interview and email the link.
    """
    # Validate Bank
    bank = session.get(QuestionBank, schedule_data.bank_id)
    if not bank or bank.admin_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid Question Bank ID")

    # Validate Candidate
    candidate = session.get(User, schedule_data.candidate_id)
    if not candidate or candidate.role != UserRole.CANDIDATE:
         raise HTTPException(status_code=400, detail="Invalid Candidate ID")

    # Availability Check (Optional - can be expanded later)
    # Check if candidate has conflicting interview within + - 1 hour? SKIPPED for MVP.

    new_session = InterviewSession(
        admin_id=current_user.id,
        candidate_id=schedule_data.candidate_id,
        bank_id=schedule_data.bank_id,
        schedule_time=schedule_data.schedule_time,
        duration_minutes=schedule_data.duration_minutes,
        status=InterviewStatus.SCHEDULED
    )
    
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    
    # Generate Link
    # Note: host needs to be configurable in real prod, assume localhost:8000 for now or passed in env
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    link = f"{base_url}/interview/access/{new_session.access_token}"
    
    # Send Email
    success = email_service.send_interview_invitation(
        to_email=candidate.email, 
        candidate_name=candidate.full_name,
        link=link,
        time_str=new_session.schedule_time.isoformat(),
        duration_minutes=new_session.duration_minutes
    )
    
    warning = None if success else "Email failed to send. Check server logs for mock link."
    
    return InterviewLinkResponse(
        session_id=new_session.id,
        access_token=new_session.access_token,
        link=link,
        scheduled_at=new_session.schedule_time.isoformat(),
        warning=warning
    )

@router.get("/interviews", response_model=List[SessionRead])
async def list_interviews(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """List interviews created by this admin."""
    # Find sessions where admin_id matches current user
    sessions = session.exec(
        select(InterviewSession)
        .where(InterviewSession.admin_id == current_user.id)
        .order_by(InterviewSession.schedule_time.desc())
    ).all()
    
    results = []
    for s in sessions:
        results.append(SessionRead(
            id=s.id,
            candidate_name=s.candidate.full_name if s.candidate else "Unknown",
            status=s.status.value,
            scheduled_at=s.schedule_time.isoformat(),
            score=s.total_score
        ))
    return results

@router.get("/candidates", response_model=List[UserRead])
async def list_candidates(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """List all users with CANDIDATE role."""
    candidates = session.exec(select(User).where(User.role == UserRole.CANDIDATE)).all()
    return candidates


# --- Results & Proctoring ---

@router.get("/users/results", response_model=List[DetailedResult])
async def get_all_results(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """API for the admin dashboard: Returns all candidate details and their interview results/audit logs."""
    # Only show sessions created by this admin
    sessions = session.exec(select(InterviewSession).where(InterviewSession.admin_id == current_user.id)).all()
    
    results = []
    for s in sessions:
        responses = s.responses
        proctoring = s.proctoring_events
        
        avg_score = sum([r.score for r in responses if r.score is not None]) / len(responses) if responses else 0
        
        results.append(DetailedResult(
            session_id=s.id,
            candidate=s.candidate.full_name if s.candidate else (s.candidate_name or "Unknown"),
            date=s.schedule_time.strftime("%Y-%m-%d %H:%M"),
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
    """Graceful shutdown trigger."""
    if current_user.role != UserRole.SUPER_ADMIN: raise HTTPException(status_code=403)
    
    # Graceful shutdown for Uvicorn
    import signal
    os.kill(os.getpid(), signal.SIGTERM) # SIGTERM allows cleaning up
    return {"message": "Server shutting down..."}
