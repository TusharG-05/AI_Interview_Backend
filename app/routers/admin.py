from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import QuestionPaper, Questions, InterviewSession, InterviewResponse, User, UserRole, ProctoringEvent, InterviewStatus
from ..auth.dependencies import get_admin_user
from ..auth.security import get_password_hash
from ..services.nlp import NLPService
from ..services.email import EmailService
from ..schemas.requests import QuestionCreate, UserCreate, InterviewScheduleCreate, PaperUpdate, QuestionUpdate
from ..schemas.responses import PaperRead, SessionRead, UserRead, DetailedResult, ResponseDetail, ProctoringLogItem, InterviewLinkResponse
import os
import shutil
import uuid
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])
nlp_service = NLPService()
email_service = EmailService()

# --- Question Paper & Question Management ---

@router.get("/papers", response_model=List[PaperRead])
async def list_papers(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all question papers created by the admin."""
    papers = session.exec(select(QuestionPaper).where(QuestionPaper.admin_id == current_user.id)).all()
    return [PaperRead(
        id=p.id, name=p.name, description=p.description, 
        question_count=len(p.questions), created_at=p.created_at.isoformat()
    ) for p in papers]

class PaperCreate(BaseModel):
    name: str
    description: Optional[str] = None



@router.post("/papers", response_model=PaperRead)
async def create_paper(
    paper_data: PaperCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new collection of questions."""
    new_paper = QuestionPaper(
        name=paper_data.name,
        description=paper_data.description,
        admin_id=current_user.id
    )
    session.add(new_paper)
    session.commit()
    session.refresh(new_paper)
    return PaperRead(id=new_paper.id, name=new_paper.name, description=new_paper.description, question_count=0, created_at=new_paper.created_at.isoformat())

@router.get("/papers/{paper_id}", response_model=PaperRead)
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get details of a specific question paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperRead(
        id=paper.id, name=paper.name, description=paper.description,
        question_count=len(paper.questions), created_at=paper.created_at.isoformat()
    )

@router.patch("/papers/{paper_id}", response_model=PaperRead)
async def update_paper(
    paper_id: int,
    paper_update: PaperUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a question paper's name or description."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    update_data = paper_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(paper, key, value)
    
    session.add(paper)
    session.commit()
    session.refresh(paper)
    return PaperRead(
        id=paper.id, name=paper.name, description=paper.description,
        question_count=len(paper.questions), created_at=paper.created_at.isoformat()
    )

@router.delete("/papers/{paper_id}")
async def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a question paper and all its associated questions."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    session.delete(paper)
    session.commit()
    return {"message": "Paper and all associated questions deleted"}

@router.get("/papers/{paper_id}/questions", response_model=List[Questions])
async def get_paper_questions(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all questions within a specific paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper.questions

@router.post("/papers/{paper_id}/questions", response_model=Questions)
async def add_question_to_paper(
    paper_id: int,
    q_data: QuestionCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """API for manually adding a new interview question to a paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    new_q = Questions(
        paper_id=paper_id,
        content=q_data.content,
        question_text=q_data.content,
        topic=q_data.topic,
        difficulty=q_data.difficulty,
        marks=q_data.marks,
        response_type=q_data.response_type
    )
    session.add(new_q)
    session.commit()
    session.refresh(new_q)
    return new_q

@router.post("/upload-doc")
async def upload_document(
    paper_id: int,
    file: UploadFile = File(...), 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Extract questions from an uploaded document (Resume/Job Desc/Excel)."""
    # Verify paper belongs to admin if provided
    if paper_id:
        paper = session.get(QuestionPaper, paper_id)
        if not paper or paper.admin_id != current_user.id:
            raise HTTPException(status_code=404, detail="Paper not found")

    # 1. Validation (DoS Prevention)
    allowed_exts = ('.pdf', '.txt', '.docx', '.xlsx', '.xls')
    if not file.filename.lower().endswith(allowed_exts):
         raise HTTPException(status_code=400, detail=f"Supported formats: {', '.join(allowed_exts)}")
    
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
        # Default to questions_only extraction
        extracted_data = nlp_service.extract_qa_from_file(file_path, questions_only=True)
        for item in extracted_data:
            q = Questions(
                paper_id=paper_id,
                content=item['question'], 
                question_text=item['question'], 
                topic="Uploaded Document",
                response_type="audio" # Default for extracted
            )
            session.add(q)
        session.commit()
        return {"message": f"Successfully extracted and added {len(extracted_data)} questions to paper {paper_id if paper_id else 'General'}"}
    finally:
        if os.path.exists(file_path): os.remove(file_path)

@router.delete("/questions/{q_id}")
async def delete_question(
    q_id: int, 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    q = session.get(Questions, q_id)
    if not q: raise HTTPException(status_code=404, detail="Question not found")
    session.delete(q)
    session.commit()
    return {"message": "Question deleted"}

@router.get("/questions", response_model=List[Questions])
async def list_all_questions(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all questions across all papers owned by the admin (including global ones)."""
    # Use outer join to include questions without a paper_id
    stmt = (
        select(Questions)
        .join(QuestionPaper, isouter=True)
        .where((QuestionPaper.admin_id == current_user.id) | (Questions.paper_id == None))
    )
    questions = session.exec(stmt).all()
    return questions

@router.get("/questions/{q_id}", response_model=Questions)
async def get_question(
    q_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get details of a specific question."""
    q = session.get(Questions, q_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    # Verify the question belongs to a paper owned by the admin
    if q.paper.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this question")
    return q

@router.patch("/questions/{q_id}", response_model=Questions)
async def update_question(
    q_id: int,
    q_update: QuestionUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update specific fields of a question."""
    q = session.get(Questions, q_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    # Verify the question belongs to a paper owned by the admin
    if q.paper.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this question")
    
    update_data = q_update.dict(exclude_unset=True)
    if "content" in update_data:
        q.question_text = update_data["content"] # Keep legacy text in sync
        
    for key, value in update_data.items():
        setattr(q, key, value)
    
    session.add(q)
    session.commit()
    session.refresh(q)
    return q

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
    # Validate Paper
    paper = session.get(QuestionPaper, schedule_data.paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid Question Paper ID")

    # Validate Candidate
    candidate = session.get(User, schedule_data.candidate_id)
    if not candidate or candidate.role != UserRole.CANDIDATE:
         raise HTTPException(status_code=400, detail="Invalid Candidate ID")

    # Availability Check (Optional - can be expanded later)
    # Check if candidate has conflicting interview within + - 1 hour? SKIPPED for MVP.

    new_session = InterviewSession(
        admin_id=current_user.id,
        candidate_id=schedule_data.candidate_id,
        paper_id=schedule_data.paper_id,
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
        
        valid_scores = [r.score for r in responses if r.score is not None]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        details = []
        for r in responses:
            res_status = "Skipped"
            if r.score is not None:
                res_status = "Answered"
            elif r.answer_text or r.transcribed_text or r.audio_path:
                res_status = "Pending AI"
                
            details.append(ResponseDetail(
                question=r.question.question_text or r.question.content or "Dynamic",
                answer=r.answer_text or r.transcribed_text or "[No Answer]",
                score=f"{round(r.score * 100, 1) if r.score is not None else 0}%",
                status=res_status
            ))

        results.append(DetailedResult(
            session_id=s.id,
            candidate=s.candidate.full_name if s.candidate else (s.candidate_name or "Unknown"),
            date=s.schedule_time.strftime("%Y-%m-%d %H:%M"),
            score=f"{round(avg_score * 100, 1)}%",
            flags=len(proctoring) > 0,
            details=details,
            proctoring_logs=[ProctoringLogItem(
                type=e.event_type,
                time=e.timestamp.strftime("%H:%M:%S"),
                details=e.details
            ) for e in proctoring]
        ))
    return results

# --- Identity & System ---



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
    
    # Permission Check: Only Super Admin can create another Super Admin
    if user_data.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Only Super Admins can create other Super Admins"
        )
    
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
