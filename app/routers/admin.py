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
from ..schemas.requests import QuestionCreate, UserCreate, InterviewScheduleCreate, PaperUpdate, QuestionUpdate, InterviewUpdate, UserUpdate, ResultUpdate
from ..schemas.responses import PaperRead, SessionRead, UserRead, DetailedResult, ResponseDetail, ProctoringLogItem, InterviewLinkResponse, InterviewDetailRead, UserDetailRead
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
        max_questions=schedule_data.max_questions,
        status=InterviewStatus.SCHEDULED
    )
    
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    
    # Random Question Selection
    import random
    from ..models.db_models import SessionQuestion
    
    # Get all questions from the paper
    available_questions = session.exec(
        select(Questions).where(Questions.paper_id == schedule_data.paper_id)
    ).all()
    
    if not available_questions:
        raise HTTPException(status_code=400, detail="Question paper has no questions")
    
    # Apply question limit if specified
    if schedule_data.max_questions:
        if schedule_data.max_questions <= 0:
            raise HTTPException(status_code=400, detail="max_questions must be greater than 0")
        
        if schedule_data.max_questions > len(available_questions):
            raise HTTPException(
                status_code=400,
                detail=f"Requested {schedule_data.max_questions} questions but only {len(available_questions)} available in this paper"
            )
        
        # Random selection
        selected_questions = random.sample(available_questions, schedule_data.max_questions)
    else:
        # Use all questions
        selected_questions = available_questions
    
    # Create SessionQuestion records with sort order
    for idx, question in enumerate(selected_questions):
        session_question = SessionQuestion(
            session_id=new_session.id,
            question_id=question.id,
            sort_order=idx
        )
        session.add(session_question)
    
    session.commit()
    
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

@router.get("/interviews/{session_id}", response_model=InterviewDetailRead)
async def get_interview(
    session_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get detailed information about a specific interview session."""
    # Retrieve the interview session
    interview_session = session.get(InterviewSession, session_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to access this interview session"
        )
    
    # Build detailed response
    return InterviewDetailRead(
        id=interview_session.id,
        candidate_id=interview_session.candidate_id,
        candidate_name=interview_session.candidate.full_name if interview_session.candidate else "Unknown",
        candidate_email=interview_session.candidate.email if interview_session.candidate else "Unknown",
        paper_id=interview_session.paper_id,
        paper_name=interview_session.paper.name if interview_session.paper else "Unknown",
        schedule_time=interview_session.schedule_time.isoformat(),
        duration_minutes=interview_session.duration_minutes,
        status=interview_session.status.value,
        total_score=interview_session.total_score,
        start_time=interview_session.start_time.isoformat() if interview_session.start_time else None,
        end_time=interview_session.end_time.isoformat() if interview_session.end_time else None,
        access_token=interview_session.access_token,
        response_count=len(interview_session.responses),
        proctoring_event_count=len(interview_session.proctoring_events)
    )

@router.patch("/interviews/{session_id}", response_model=InterviewDetailRead)
async def update_interview(
    session_id: int,
    update_data: InterviewUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update interview session details (schedule_time, duration, status, paper)."""
    # Retrieve the interview session
    interview_session = session.get(InterviewSession, session_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to modify this interview session"
        )
    
    # Prevent updates to live or completed interviews (business rule)
    if interview_session.status in [InterviewStatus.LIVE, InterviewStatus.COMPLETED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot update interview with status '{interview_session.status.value}'. Only scheduled interviews can be modified."
        )
    
    # Apply updates
    update_dict = update_data.dict(exclude_unset=True)
    
    # Validate paper_id if provided
    if "paper_id" in update_dict:
        paper = session.get(QuestionPaper, update_dict["paper_id"])
        if not paper or paper.admin_id != current_user.id:
            raise HTTPException(status_code=400, detail="Invalid Question Paper ID")
    
    # Validate and convert schedule_time if provided
    if "schedule_time" in update_dict:
        from datetime import datetime
        try:
            update_dict["schedule_time"] = datetime.fromisoformat(update_dict["schedule_time"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid schedule_time format. Use ISO format.")
    
    # Validate status if provided
    if "status" in update_dict:
        try:
            update_dict["status"] = InterviewStatus(update_dict["status"])
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in InterviewStatus])}"
            )
    
    # Handle max_questions update (re-select questions if changed)
    if "max_questions" in update_dict:
        import random
        from ..models.db_models import SessionQuestion
        
        new_max = update_dict["max_questions"]
        
        # Validation
        if new_max is not None and new_max <= 0:
            raise HTTPException(status_code=400, detail="max_questions must be greater than 0")
        
        # Get available questions
        available_questions = session.exec(
            select(Questions).where(Questions.paper_id == interview_session.paper_id)
        ).all()
        
        if new_max and new_max > len(available_questions):
            raise HTTPException(
                status_code=400,
                detail=f"Requested {new_max} questions but only {len(available_questions)} available"
            )
        
        # Delete existing SessionQuestion records
        existing_session_questions = session.exec(
            select(SessionQuestion).where(SessionQuestion.session_id == session_id)
        ).all()
        
        for sq in existing_session_questions:
            session.delete(sq)
        
        # Re-select questions
        if new_max:
            selected_questions = random.sample(available_questions, new_max)
        else:
            selected_questions = available_questions
        
        # Create new SessionQuestion records
        for idx, question in enumerate(selected_questions):
            session_question = SessionQuestion(
                session_id=session_id,
                question_id=question.id,
                sort_order=idx
            )
            session.add(session_question)
    
    # Update the session
    for key, value in update_dict.items():
        setattr(interview_session, key, value)
    
    session.add(interview_session)
    session.commit()
    session.refresh(interview_session)
    
    # Return updated interview details
    return InterviewDetailRead(
        id=interview_session.id,
        candidate_id=interview_session.candidate_id,
        candidate_name=interview_session.candidate.full_name if interview_session.candidate else "Unknown",
        candidate_email=interview_session.candidate.email if interview_session.candidate else "Unknown",
        paper_id=interview_session.paper_id,
        paper_name=interview_session.paper.name if interview_session.paper else "Unknown",
        schedule_time=interview_session.schedule_time.isoformat(),
        duration_minutes=interview_session.duration_minutes,
        status=interview_session.status.value,
        total_score=interview_session.total_score,
        start_time=interview_session.start_time.isoformat() if interview_session.start_time else None,
        end_time=interview_session.end_time.isoformat() if interview_session.end_time else None,
        access_token=interview_session.access_token,
        response_count=len(interview_session.responses),
        proctoring_event_count=len(interview_session.proctoring_events)
    )

@router.delete("/interviews/{session_id}")
async def delete_interview(
    session_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Cancel/delete an interview session (soft delete by setting status to CANCELLED)."""
    # Retrieve the interview session
    interview_session = session.get(InterviewSession, session_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this interview session"
        )
    
    # Soft delete: set status to CANCELLED instead of hard deleting
    # This preserves audit trail and allows for potential recovery
    interview_session.status = InterviewStatus.CANCELLED
    session.add(interview_session)
    session.commit()
    
    return {
        "message": "Interview session cancelled successfully",
        "session_id": session_id,
        "candidate": interview_session.candidate.full_name if interview_session.candidate else "Unknown",
        "scheduled_time": interview_session.schedule_time.isoformat()
    }

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

@router.get("/results/{session_id}", response_model=DetailedResult)
async def get_result(
    session_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get detailed result for a specific interview session."""
    # Get the interview session
    interview_session = session.get(InterviewSession, session_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this result"
        )
    
    # Build detailed result (reuse logic from get_all_results)
    responses = interview_session.responses
    proctoring = interview_session.proctoring_events
    
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
    
    return DetailedResult(
        session_id=interview_session.id,
        candidate=interview_session.candidate.full_name if interview_session.candidate else (interview_session.candidate_name or "Unknown"),
        date=interview_session.schedule_time.strftime("%Y-%m-%d %H:%M"),
        score=f"{round(avg_score * 100, 1)}%",
        flags=len(proctoring) > 0,
        details=details,
        proctoring_logs=[ProctoringLogItem(
            type=e.event_type,
            time=e.timestamp.strftime("%H:%M:%S"),
            details=e.details
        ) for e in proctoring]
    )

@router.patch("/results/{session_id}", response_model=DetailedResult)
async def update_result(
    session_id: int,
    update_data: ResultUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update result scores and evaluations."""
    # Get the interview session
    interview_session = session.get(InterviewSession, session_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to modify this result"
        )
    
    # Business rule: Cannot update SCHEDULED interviews (no results yet)
    if interview_session.status == InterviewStatus.SCHEDULED:
        raise HTTPException(
            status_code=400,
            detail="Cannot update results for scheduled interviews. Interview must be in progress or completed."
        )
    
    # Business rule: Cannot update CANCELLED interviews
    if interview_session.status == InterviewStatus.CANCELLED:
        raise HTTPException(
            status_code=400,
            detail="Cannot update results for cancelled interviews."
        )
    
    update_dict = update_data.dict(exclude_unset=True)
    
    # Update total score if provided
    if "total_score" in update_dict:
        interview_session.total_score = update_dict["total_score"]
    
    # Update individual responses if provided
    if "responses" in update_dict and update_dict["responses"]:
        for resp_update in update_dict["responses"]:
            response_id = resp_update.get("response_id")
            
            # Get the response
            interview_response = session.get(InterviewResponse, response_id)
            
            if not interview_response:
                raise HTTPException(
                    status_code=400,
                    detail=f"Response with ID {response_id} not found"
                )
            
            # Verify response belongs to this session
            if interview_response.session_id != session_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Response {response_id} does not belong to session {session_id}"
                )
            
            # Update score if provided
            if "score" in resp_update and resp_update["score"] is not None:
                interview_response.score = resp_update["score"]
            
            # Update evaluation text if provided
            if "evaluation_text" in resp_update and resp_update["evaluation_text"] is not None:
                interview_response.evaluation_text = resp_update["evaluation_text"]
            
            session.add(interview_response)
    
    # Save changes
    session.add(interview_session)
    session.commit()
    session.refresh(interview_session)
    
    # Return updated result using GET logic
    return await get_result(session_id, current_user, session)

@router.delete("/results/{session_id}")
async def delete_result(
    session_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete all result data for an interview session (hard delete responses, keep session)."""
    # Get the interview session
    interview_session = session.get(InterviewSession, session_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this result"
        )
    
    # Count responses before deletion
    response_count = len(interview_session.responses)
    
    # Delete all responses for this session
    for response in interview_session.responses:
        session.delete(response)
    
    # Clear total score
    interview_session.total_score = None
    
    session.add(interview_session)
    session.commit()
    
    return {
        "message": "Result data deleted successfully",
        "session_id": session_id,
        "responses_deleted": response_count,
        "note": "Interview session preserved, only result data removed"
    }

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

@router.get("/users/{user_id}", response_model=UserDetailRead)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get detailed information about a specific user."""
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count interviews created as admin
    created_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all()
    
    # Count interviews participated as candidate
    participated_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all()
    
    return UserDetailRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        resume_text=user.resume_text,
        has_profile_image=user.profile_image_bytes is not None,
        has_face_embedding=user.face_embedding is not None,
        created_interviews_count=len(created_interviews),
        participated_interviews_count=len(participated_interviews)
    )

@router.patch("/users/{user_id}", response_model=UserDetailRead)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update user details with role change protections."""
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_dict = update_data.dict(exclude_unset=True)
    
    # Email uniqueness validation
    if "email" in update_dict and update_dict["email"] != user.email:
        existing_user = session.exec(
            select(User).where(User.email == update_dict["email"])
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Password hashing
    if "password" in update_dict:
        update_dict["password_hash"] = get_password_hash(update_dict.pop("password"))
    
    # Role change validation
    if "role" in update_dict:
        try:
            new_role = UserRole(update_dict["role"])
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}"
            )
        
        # Protection 1: Only SUPER_ADMIN can promote to SUPER_ADMIN
        if new_role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Only Super Admins can promote users to Super Admin"
            )
        
        # Protection 2: Prevent demoting the last SUPER_ADMIN
        if user.role == UserRole.SUPER_ADMIN and new_role != UserRole.SUPER_ADMIN:
            # Count active SUPER_ADMINs
            super_admin_count = session.exec(
                select(User).where(User.role == UserRole.SUPER_ADMIN, User.is_active == True)
            ).all()
            
            if len(super_admin_count) <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last Super Admin. Promote another user first."
                )
        
        # Protection 3: Prevent self-demotion from SUPER_ADMIN
        if user.id == current_user.id and user.role == UserRole.SUPER_ADMIN and new_role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote yourself from Super Admin role"
            )
        
        update_dict["role"] = new_role
    
    # Apply updates
    for key, value in update_dict.items():
        setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Return updated user details
    created_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all()
    participated_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all()
    
    return UserDetailRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        resume_text=user.resume_text,
        has_profile_image=user.profile_image_bytes is not None,
        has_face_embedding=user.face_embedding is not None,
        created_interviews_count=len(created_interviews),
        participated_interviews_count=len(participated_interviews)
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Soft delete a user by setting is_active to False."""
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Protection 1: Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    # Protection 2: Prevent deleting the last SUPER_ADMIN
    if user.role == UserRole.SUPER_ADMIN:
        super_admin_count = session.exec(
            select(User).where(User.role == UserRole.SUPER_ADMIN, User.is_active == True)
        ).all()
        
        if len(super_admin_count) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last Super Admin. Promote another user first."
            )
    
    # Soft delete: set is_active to False
    user.is_active = False
    session.add(user)
    session.commit()
    
    return {
        "message": "User deactivated successfully",
        "user_id": user_id,
        "email": user.email,
        "full_name": user.full_name
    }

@router.post("/shutdown")
def shutdown(current_user: User = Depends(get_admin_user)):
    """Graceful shutdown trigger."""
    if current_user.role != UserRole.SUPER_ADMIN: raise HTTPException(status_code=403)
    
    # Graceful shutdown for Uvicorn
    import signal
    os.kill(os.getpid(), signal.SIGTERM) # SIGTERM allows cleaning up
    return {"message": "Server shutting down..."}
