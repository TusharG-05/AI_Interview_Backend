from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from ..core.database import get_db as get_session
from ..models.db_models import QuestionPaper, Questions, InterviewSession, Answers, InterviewResult, User, UserRole, ProctoringEvent, InterviewStatus
from ..auth.dependencies import get_admin_user
from ..auth.security import get_password_hash
from ..services.nlp import NLPService
from ..services.email import EmailService
from ..core.config import APP_BASE_URL, MAIL_USERNAME, MAIL_PASSWORD
from ..core.logger import get_logger

logger = get_logger(__name__)

from ..schemas.requests import (
    QuestionCreate, UserCreate, InterviewScheduleCreate, PaperUpdate, 
    QuestionUpdate, InterviewUpdate, UserUpdate, ResultUpdate
)
from ..schemas.responses import (
    PaperRead, QuestionRead, SessionRead, UserRead, DetailedResult, 
    ResponseDetail, ProctoringLogItem, InterviewLinkResponse, 
    InterviewDetailRead, UserDetailRead, CandidateStatusResponse, 
    LiveStatusItem, AnswerRead, InterviewSessionDetail
)
from ..schemas.interview_result import (
    InterviewResultDetail, InterviewSessionNested, UserNested, QuestionPaperNested, AnswersNested, QuestionNested
)
from ..schemas.api_response import ApiResponse
from ..schemas.user_schemas import serialize_user, serialize_user_flat
import os
import shutil
import uuid
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])
nlp_service = NLPService()
email_service = EmailService()

# --- WebSocket Dashboard ---
from ..services.websocket_manager import manager
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/dashboard/ws")
async def admin_dashboard_ws(websocket: WebSocket, token: str = None):
    """
    Real-time Admin Dashboard Stream.
    Requires Admin Authentication (Token passed as query param).
    """
    # TODO: Validate Token (skipped for MVP speed, assume valid if they know endpoint)
    # real_user = get_current_user(token=token) ...
    
    await manager.connect_admin(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)

# --- Question Paper & Question Management ---

@router.get("/papers", response_model=ApiResponse[List[PaperRead]])
async def list_papers(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all question papers created by the admin."""
    papers = session.exec(select(QuestionPaper).where(QuestionPaper.admin_id == current_user.id)).all()
    papers_data = [PaperRead(
        id=p.id, name=p.name, description=p.description, 
        question_count=len(p.questions), 
        questions=[QuestionRead(
            id=q.id, content=q.content, question_text=q.question_text,
            topic=q.topic, difficulty=q.difficulty, marks=q.marks,
            response_type=q.response_type
        ) for q in p.questions],
        created_at=p.created_at.isoformat(),
        created_by=serialize_user(p.admin, fallback_role="admin")
    ) for p in papers]
    return ApiResponse(
        status_code=200,
        data=papers_data,
        message="Question papers retrieved successfully"
    )

from pydantic import BaseModel, Field

class PaperCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the question paper")
    description: Optional[str] = None



@router.post("/papers", response_model=ApiResponse[PaperRead], status_code=201)
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
    try:
        session.commit()
        session.refresh(new_paper)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create paper: {str(e)}")
    paper_read = PaperRead(
        id=new_paper.id, name=new_paper.name, description=new_paper.description, 
        question_count=0, questions=[], created_at=new_paper.created_at.isoformat(),
        created_by=serialize_user(current_user)
    )
    return ApiResponse(
        status_code=201,
        data=paper_read,
        message="Question paper created successfully"
    )

@router.get("/papers/{paper_id}", response_model=ApiResponse[PaperRead])
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get details of a specific question paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    paper_read = PaperRead(
        id=paper.id, name=paper.name, description=paper.description,
        question_count=len(paper.questions),
        questions=[QuestionRead(
            id=q.id, content=q.content, question_text=q.question_text,
            topic=q.topic, difficulty=q.difficulty, marks=q.marks,
            response_type=q.response_type
        ) for q in paper.questions],
        created_at=paper.created_at.isoformat(),
        created_by=serialize_user(paper.admin, fallback_role="admin")
    )
    return ApiResponse(
        status_code=200,
        data=paper_read,
        message="Question paper retrieved successfully"
    )

@router.patch("/papers/{paper_id}", response_model=ApiResponse[PaperRead])
async def update_paper(
    paper_id:int,
    paper_update: PaperUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a question paper's name or description."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    update_data = paper_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(paper, key, value)
    
    session.add(paper)
    try:
        session.commit()
        session.refresh(paper)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update paper: {str(e)}")
    paper_read = PaperRead(
        id=paper.id, name=paper.name, description=paper.description,
        question_count=len(paper.questions),
        questions=[QuestionRead(
            id=q.id, content=q.content, question_text=q.question_text,
            topic=q.topic, difficulty=q.difficulty, marks=q.marks,
            response_type=q.response_type
        ) for q in paper.questions],
        created_at=paper.created_at.isoformat(),
        created_by=serialize_user(paper.admin, fallback_role="admin")
    )
    return ApiResponse(
        status_code=200,
        data=paper_read,
        message="Question paper updated successfully"
    )

@router.delete("/papers/{paper_id}", response_model=ApiResponse[dict])
async def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete a question paper and all its associated questions."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check for existing sessions using this paper
    existing_sessions = session.exec(select(InterviewSession).where(InterviewSession.paper_id == paper_id)).first()
    if existing_sessions:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete paper because it is used in scheduled or completed interviews."
        )
    
    session.delete(paper)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete paper: {str(e)}")
    return ApiResponse(
        status_code=200,
        data={},
        message="Paper and all associated questions deleted successfully"
    )


@router.post("/papers/{paper_id}/questions", response_model=ApiResponse[Questions], status_code=201)
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
    try:
        session.commit()
        session.refresh(new_q)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create question: {str(e)}")
    return ApiResponse(
        status_code=201,
        data=new_q,
        message="Question added to paper successfully"
    )

@router.get("/papers/{paper_id}/questions", response_model=ApiResponse[List[Questions]])
async def list_paper_questions(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """List all questions belonging to a specific question paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper or paper.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Paper not found")
    questions = session.exec(select(Questions).where(Questions.paper_id == paper_id)).all()
    return ApiResponse(
        status_code=200,
        data=questions,
        message=f"Questions for paper '{paper.name}' retrieved successfully"
    )

@router.post("/upload-doc", response_model=ApiResponse[dict])
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
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to upload questions: {str(e)}")
        return ApiResponse(
            status_code=200,
            data={"questions_count": len(extracted_data)},
            message=f"Successfully extracted and added {len(extracted_data)} questions to paper"
        )
    finally:
        if os.path.exists(file_path): os.remove(file_path)

@router.delete("/questions/{q_id}", response_model=ApiResponse[dict])
async def delete_question(
    q_id: int, 
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    q = session.get(Questions, q_id)
    if not q: raise HTTPException(status_code=404, detail="Question not found")
    session.delete(q)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete question: {str(e)}")
    return ApiResponse(
        status_code=200,
        data={},
        message="Question deleted successfully"
    )

@router.get("/questions", response_model=ApiResponse[List[Questions]])
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
    return ApiResponse(
        status_code=200,
        data=questions,
        message="Questions retrieved successfully"
    )

@router.get("/questions/{q_id}", response_model=ApiResponse[Questions])
async def get_question(
    q_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get details of a specific question."""
    q = session.get(Questions, q_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    # Verify the question belongs to a paper owned by the admin (or is orphaned)
    if q.paper and q.paper.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this question")
    return ApiResponse(
        status_code=200,
        data=q,
        message="Question retrieved successfully"
    )

@router.patch("/questions/{q_id}", response_model=ApiResponse[Questions])
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
    # Verify the question belongs to a paper owned by the admin (or is orphaned)
    if q.paper and q.paper.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this question")
    
    update_data = q_update.model_dump(exclude_unset=True)
    if "content" in update_data:
        q.question_text = update_data["content"] # Keep legacy text in sync
        
    for key, value in update_data.items():
        setattr(q, key, value)
    
    session.add(q)
    try:
        session.commit()
        session.refresh(q)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update question: {str(e)}")
    return ApiResponse(
        status_code=200,
        data=q,
        message="Question updated successfully"
    )

# --- Interview Scheduling ---

@router.post("/interviews/schedule", response_model=ApiResponse[InterviewLinkResponse], status_code=201)
async def schedule_interview(
    schedule_data: InterviewScheduleCreate, 
    background_tasks: BackgroundTasks,
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

    # Parse schedule time
    try:
        # Handle "Z" for UTC if present, though fromisoformat supports it in newer Python versions
        dt_str = schedule_data.schedule_time.replace("Z", "+00:00")
        schedule_dt = datetime.fromisoformat(dt_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid schedule_time format. ISO 8601 expected.")

    new_session = InterviewSession(
        admin_id=current_user.id,
        candidate_id=schedule_data.candidate_id,
        paper_id=schedule_data.paper_id,
        schedule_time=schedule_dt,
        duration_minutes=schedule_data.duration_minutes,
        max_questions=schedule_data.max_questions,
        status=InterviewStatus.SCHEDULED
    )
    
    session.add(new_session)
    try:
        session.commit()
        session.refresh(new_session)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to schedule interview: {str(e)}")
    
    # Track initial status - INVITED
    from ..services.status_manager import record_status_change
    from ..models.db_models import CandidateStatus
    
    record_status_change(
        session=session,
        interview_session=new_session,
        new_status=CandidateStatus.INVITED,
        metadata={
            "admin_id": current_user.id,
            "candidate_id": schedule_data.candidate_id,
            "email_sent": True
        }
    )

    # Email Invitation will be sent at the end using BackgroundTasks
    
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
            interview_id=new_session.id,
            question_id=question.id,
            sort_order=idx
        )
        session.add(session_question)
    
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign questions: {str(e)}")
    
    # Generate Link
    from ..core.config import APP_BASE_URL
    link = f"{APP_BASE_URL}/interview/access/{new_session.access_token}"
    
    # Send Email Invitation Asynchronously (prevent UI hang)
    background_tasks.add_task(
        email_service.send_interview_invitation,
        to_email=candidate.email, 
        candidate_name=candidate.full_name,
        link=link,
        time_str=new_session.schedule_time.isoformat(),
        duration_minutes=new_session.duration_minutes
    )
    
    warning = "Email invitation queued for sending."
    
    # Serialize users with role-based keys
    admin_dict = serialize_user(current_user)  # {"admin": {...}}
    candidate_dict = serialize_user(candidate)  # {"candidate": {...}}
    
    
    # Construct InterviewSessionDetail
    interview_detail = InterviewSessionDetail(
        id=new_session.id,
        access_token=new_session.access_token,
        admin_id=new_session.admin_id,
        candidate_id=new_session.candidate_id,
        paper_id=new_session.paper_id,
        schedule_time=new_session.schedule_time.isoformat(),
        duration_minutes=new_session.duration_minutes,
        max_questions=new_session.max_questions,
        start_time=new_session.start_time.isoformat() if new_session.start_time else None,
        end_time=new_session.end_time.isoformat() if new_session.end_time else None,
        status=new_session.status.value,
        total_score=new_session.total_score,
        current_status=new_session.current_status.value if new_session.current_status else None,
        last_activity=new_session.last_activity.isoformat() if new_session.last_activity else None,
        warning_count=new_session.warning_count,
        max_warnings=new_session.max_warnings,
        is_suspended=new_session.is_suspended,
        suspension_reason=new_session.suspension_reason,
        suspended_at=new_session.suspended_at.isoformat() if new_session.suspended_at else None,
        enrollment_audio_path=new_session.enrollment_audio_path,
        candidate_name=candidate.full_name,
        admin_name=current_user.full_name,
        is_completed=new_session.is_completed
    )

    link_response = InterviewLinkResponse(
        interview=interview_detail,
        admin=admin_dict,
        candidate=candidate_dict,
        access_token=new_session.access_token,
        link=link,
        scheduled_at=new_session.schedule_time.isoformat(),
        warning=warning
    )
    return ApiResponse(
        status_code=201,
        data=link_response,
        message="Interview scheduled successfully"
    )

@router.get("/interviews", response_model=ApiResponse[List[SessionRead]])
async def list_interviews(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """List interviews created by this admin."""
    # Only show sessions created by this admin (including those where admin is NULL)
    sessions = session.exec(
        select(InterviewSession)
        .where(
            (InterviewSession.admin_id == current_user.id) | 
            (InterviewSession.admin_id == None)
        )
        .options(
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.candidate)
        )
    ).all()
    
    results = []
    for s in sessions:
        # Serialize users with role-based keys, handling NULL users
        admin_dict = serialize_user(s.admin, fallback_name=s.admin_name, fallback_role="admin")
        candidate_dict = serialize_user(s.candidate, fallback_name=s.candidate_name, fallback_role="candidate")
        
        results.append(SessionRead(
            id=s.id,
            admin=admin_dict,
            candidate=candidate_dict,
            status=s.status.value,
            scheduled_at=s.schedule_time.isoformat(),
            score=s.total_score
        ))
    return ApiResponse(
        status_code=200,
        data=results,
        message="Interviews retrieved successfully"
    )

@router.get("/interviews/live-status", response_model=ApiResponse[List[LiveStatusItem]])
async def get_live_status_dashboard(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get lightweight status summary for all active interviews.
    
    Shows all interviews that are NOT completed/cancelled/expired.
    Useful for admin dashboard to monitor multiple concurrent interviews.
    
    Returns:
        List of active interviews with basic status, warnings, and progress
    """
    from ..models.db_models import CandidateStatus
    
    # Get all active interviews for this admin
    # Active = not completed/cancelled/suspended permanently
    stmt = select(InterviewSession).where(
        InterviewSession.admin_id == current_user.id,
        InterviewSession.status.in_([
            InterviewStatus.SCHEDULED,
            InterviewStatus.LIVE
        ])
    ).options(
        selectinload(InterviewSession.selected_questions),
        selectinload(InterviewSession.result).selectinload(InterviewResult.answers),
        selectinload(InterviewSession.candidate)
    ).order_by(InterviewSession.last_activity.desc())
    
    active_sessions = session.exec(stmt).all()
    
    results = []
    for interview_session in active_sessions:
        # Calculate progress
        total_questions = len(interview_session.selected_questions) if interview_session.selected_questions else 0
        responses = interview_session.result.answers if interview_session.result else []
        answered_questions = len(responses)
        progress_percent = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Serialize candidate
        candidate_dict = serialize_user(interview_session.candidate)
        
        # Serialize interview
        # Serialize interview
        interview_dict = {
            "id": interview_session.id,
            "access_token": interview_session.access_token,
            "admin_id": interview_session.admin_id,
            "candidate_id": interview_session.candidate_id,
            "paper_id": interview_session.paper_id,
            "schedule_time": interview_session.schedule_time.isoformat(),
            "duration_minutes": interview_session.duration_minutes,
            "max_questions": interview_session.max_questions,
            "start_time": interview_session.start_time.isoformat() if interview_session.start_time else None,
            "end_time": interview_session.end_time.isoformat() if interview_session.end_time else None,
            "status": interview_session.status.value,
            "total_score": interview_session.total_score,
            "current_status": interview_session.current_status.value if interview_session.current_status else None,
            "last_activity": interview_session.last_activity.isoformat() if interview_session.last_activity else None,
            "warning_count": interview_session.warning_count,
            "max_warnings": interview_session.max_warnings,
            "is_suspended": interview_session.is_suspended,
            "suspension_reason": interview_session.suspension_reason,
            "suspended_at": interview_session.suspended_at.isoformat() if interview_session.suspended_at else None,
            "enrollment_audio_path": interview_session.enrollment_audio_path,
            "candidate_name": interview_session.candidate.full_name if interview_session.candidate else interview_session.candidate_name,
            "admin_name": current_user.full_name, # Since we filtered by current_user.id
            "is_completed": interview_session.is_completed
        }
        
        results.append(LiveStatusItem(
            interview=interview_dict,
            candidate=candidate_dict,
            current_status=interview_session.current_status.value if interview_session.current_status else None,
            warning_count=interview_session.warning_count,
            warnings_remaining=max(0, interview_session.max_warnings - interview_session.warning_count),
            is_suspended=interview_session.is_suspended,
            last_activity=interview_session.last_activity.isoformat() if interview_session.last_activity else None,
            progress_percent=round(progress_percent, 1)
        ))
    
    return ApiResponse(
        status_code=200,
        data=results,
        message="Live interview status retrieved successfully"
    )


@router.get("/interviews/{interview_id}", response_model=ApiResponse[InterviewDetailRead])
async def get_interview(
    interview_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get detailed information about a specific interview session."""
    # Retrieve the interview session
    interview_session = session.exec(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .options(
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.result).selectinload(InterviewResult.answers),
            selectinload(InterviewSession.proctoring_events)
        )
    ).first()
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin (handle NULL admin_id)
    if interview_session.admin_id and interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to access this interview session"
        )
    
    # Serialize users with role-based keys, handling NULL users
    admin_dict = serialize_user(interview_session.admin, fallback_name=interview_session.admin_name, fallback_role="admin")
    candidate_dict = serialize_user(interview_session.candidate, fallback_name=interview_session.candidate_name, fallback_role="candidate")
    
    # Build detailed response
    detail_read = InterviewDetailRead(
        id=interview_session.id,
        admin=admin_dict,
        candidate=candidate_dict,
        paper_id=interview_session.paper_id,
        paper_name=interview_session.paper.name if interview_session.paper else "Unknown",
        schedule_time=interview_session.schedule_time.isoformat(),
        duration_minutes=interview_session.duration_minutes,
        status=interview_session.status.value,
        total_score=interview_session.total_score,
        start_time=interview_session.start_time.isoformat() if interview_session.start_time else None,
        end_time=interview_session.end_time.isoformat() if interview_session.end_time else None,
        access_token=interview_session.access_token,
        response_count=len(interview_session.result.answers) if interview_session.result else 0,
        proctoring_event_count=len(interview_session.proctoring_events),
        enrollment_audio_url=f"/api/admin/interviews/enrollment-audio/{interview_session.id}" if interview_session.enrollment_audio_path else None
    )
    return ApiResponse(
        status_code=200,
        data=detail_read,
        message="Interview details retrieved successfully"
    )

@router.patch("/interviews/{interview_id}", response_model=ApiResponse[InterviewDetailRead])
async def update_interview(
    interview_id: int,
    update_data: InterviewUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update interview session details (schedule_time, duration, status, paper)."""
    # Retrieve the interview session
    interview_session = session.get(InterviewSession, interview_id)
    
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
    update_dict = update_data.model_dump(exclude_unset=True)
    
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
            select(SessionQuestion).where(SessionQuestion.interview_id == interview_id)
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
                interview_id=interview_id,
                question_id=question.id,
                sort_order=idx
            )
            session.add(session_question)
    
    # Update the session
    for key, value in update_dict.items():
        setattr(interview_session, key, value)
    
    session.add(interview_session)
    try:
        session.commit()
        session.refresh(interview_session)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update interview: {str(e)}")
    
    # Return updated interview details
    admin_dict = serialize_user(interview_session.admin, fallback_name=interview_session.admin_name, fallback_role="admin")
    candidate_dict = serialize_user(interview_session.candidate, fallback_name=interview_session.candidate_name, fallback_role="candidate")
    
    detail_read = InterviewDetailRead(
        id=interview_session.id,
        admin=admin_dict,
        candidate=candidate_dict,
        paper_id=interview_session.paper_id,
        paper_name=interview_session.paper.name if interview_session.paper else "Unknown",
        schedule_time=interview_session.schedule_time.isoformat(),
        duration_minutes=interview_session.duration_minutes,
        status=interview_session.status.value,
        total_score=interview_session.total_score,
        start_time=interview_session.start_time.isoformat() if interview_session.start_time else None,
        end_time=interview_session.end_time.isoformat() if interview_session.end_time else None,
        access_token=interview_session.access_token,
        response_count=len(interview_session.result.answers) if interview_session.result else 0,
        proctoring_event_count=len(interview_session.proctoring_events),
        enrollment_audio_url=f"/api/admin/interviews/enrollment-audio/{interview_session.id}" if interview_session.enrollment_audio_path else None
    )
    return ApiResponse(
        status_code=200,
        data=detail_read,
        message="Interview session updated successfully"
    )

@router.delete("/interviews/{interview_id}", response_model=ApiResponse[dict])
async def delete_interview(
    interview_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Hard delete an interview session and all related data (responses, proctoring events, etc.)."""
    # Retrieve the interview session
    interview_session = session.get(InterviewSession, interview_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin (handle NULL admin_id)
    if interview_session.admin_id and interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this interview session"
        )
    
    # Store info for response before deletion
    candidate_name = interview_session.candidate.full_name if interview_session.candidate else interview_session.candidate_name or "Unknown"
    scheduled_time = interview_session.schedule_time.isoformat()
    
    # Hard delete: this will cascade to responses, proctoring_events, selected_questions, status_timeline
    session.delete(interview_session)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete interview: {str(e)}")
    
    return ApiResponse(
        status_code=200,
        data={
            "interview_id": interview_id,
            "candidate_name": candidate_name,
            "scheduled_time": scheduled_time
        },
        message="Interview session and all related data deleted successfully"
    )

@router.get("/candidates", response_model=ApiResponse[dict])
async def list_candidates(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    """List users with CANDIDATE role with pagination and search."""
    from ..schemas.user_schemas import serialize_user
    from sqlalchemy import func
    
    query = select(User)
    
    # Role-based visibility logic
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin sees both candidates and regular admins
        query = query.where(User.role.in_([UserRole.CANDIDATE, UserRole.ADMIN]))
    else:
        # Regular admin sees only candidates
        query = query.where(User.role == UserRole.CANDIDATE)
    
    if search:
        search_filter = f"%{search}%"
        # Using ilike for case-insensitive search
        query = query.where(
            (User.full_name.ilike(search_filter)) | 
            (User.email.ilike(search_filter))
        )
        
    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    
    # Apply pagination
    query = query.order_by(User.id.desc()).offset(skip).limit(limit)
    candidates = session.exec(query).all()
    
    return ApiResponse(
        status_code=200,
        data={
            "items": [serialize_user(c) for c in candidates],
            "total": total_count,
            "skip": skip,
            "limit": limit
        },
        message="Candidates retrieved successfully"
    )


# --- Results & Proctoring ---

@router.get("/users/results", response_model=ApiResponse[List[InterviewResultDetail]])
async def get_all_results(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """API for the admin dashboard: Returns all candidate details and their interview results/audit logs."""
    
    # Only show sessions created by this admin
    sessions = session.exec(
        select(InterviewSession)
        .where(InterviewSession.admin_id == current_user.id)
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.paper),
            selectinload(InterviewSession.result).selectinload(InterviewResult.answers).selectinload(Answers.question),
            selectinload(InterviewSession.admin)
        )
    ).all()
    
    results = []
    for s in sessions:
        if not s.result: continue 
        
        # Build nested objects
        # 1. Admin
        admin_obj = None
        if s.admin:
            admin_obj = UserNested(
                id=s.admin.id, email=s.admin.email, full_name=s.admin.full_name, role=s.admin.role.value,
                profile_image=s.admin.profile_image
            )
        elif s.admin_name:
             pass
             
        # 2. Candidate
        candidate_obj = None
        if s.candidate:
            candidate_obj = UserNested(
                id=s.candidate.id, email=s.candidate.email, full_name=s.candidate.full_name, role=s.candidate.role.value,
                 profile_image=s.candidate.profile_image
            )
            
        # 3. Paper
        paper_obj = None
        if s.paper:
            paper_obj = QuestionPaperNested(
                id=s.paper.id, name=s.paper.name, description=s.paper.description, 
                admin_id=s.paper.admin_id, created_at=s.paper.created_at
            )
            
        # 4. Session Nested
        session_nested = InterviewSessionNested(
            id=s.id, access_token=s.access_token,
            admin=admin_obj, candidate=candidate_obj, paper=paper_obj,
            schedule_time=s.schedule_time, duration_minutes=s.duration_minutes,
            max_questions=s.max_questions, start_time=s.start_time, end_time=s.end_time,
            status=s.status.value, total_score=s.total_score,
            current_status=s.current_status.value if s.current_status else None,
            last_activity=s.last_activity, warning_count=s.warning_count,
            max_warnings=s.max_warnings, is_suspended=s.is_suspended,
            suspension_reason=s.suspension_reason, suspended_at=s.suspended_at,
            enrollment_audio_path=s.enrollment_audio_path,
            candidate_name=s.candidate_name, admin_name=s.admin_name,
            is_completed=s.is_completed
        )
        
        # 5. Answers
        answers_nested = []
        for ans in s.result.answers:
            q_nested = None
            if ans.question:
                q_nested = QuestionNested(
                    id=ans.question.id, content=ans.question.content,
                    question_text=ans.question.question_text, topic=ans.question.topic,
                    difficulty=ans.question.difficulty, marks=ans.question.marks,
                    response_type=ans.question.response_type
                )
            
            answers_nested.append(AnswersNested(
                id=ans.id, interview_result_id=ans.interview_result_id,
                question=q_nested,
                candidate_answer=ans.candidate_answer, feedback=ans.feedback,
                score=ans.score, audio_path=ans.audio_path,
                transcribed_text=ans.transcribed_text, timestamp=ans.timestamp
            ))
            
        # 6. Top Level Result
        results.append(InterviewResultDetail(
            id=s.result.id,
            interview=session_nested,
            interview_response=answers_nested,
            total_score=s.result.total_score,
            created_at=s.result.created_at
        ))

    return ApiResponse(
        status_code=200,
        data=results,
        message="All results retrieved successfully"
    )

@router.get("/results/{interview_id}", response_model=ApiResponse[InterviewResultDetail])
async def get_result(
    interview_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Get detailed result for a specific interview session."""

    # Get the interview session
    interview_session = session.exec(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.paper),
            selectinload(InterviewSession.result).selectinload(InterviewResult.answers).selectinload(Answers.question),
            selectinload(InterviewSession.admin)
        )
    ).first()
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this result"
        )
        
    s = interview_session
    if not s.result:
         raise HTTPException(status_code=404, detail="Result not found for this interview")

    # Build nested objects
    # 1. Admin
    admin_obj = None
    if s.admin:
        admin_obj = UserNested(
            id=s.admin.id, email=s.admin.email, full_name=s.admin.full_name, role=s.admin.role.value,
            profile_image=s.admin.profile_image 
        )
         
    # 2. Candidate
    candidate_obj = None
    if s.candidate:
        candidate_obj = UserNested(
            id=s.candidate.id, email=s.candidate.email, full_name=s.candidate.full_name, role=s.candidate.role.value,
             profile_image=s.candidate.profile_image
        )
        
    # 3. Paper
    paper_obj = None
    if s.paper:
        paper_obj = QuestionPaperNested(
            id=s.paper.id, name=s.paper.name, description=s.paper.description, 
            admin_id=s.paper.admin_id, created_at=s.paper.created_at
        )
        
    # 4. Session Nested
    session_nested = InterviewSessionNested(
        id=s.id, access_token=s.access_token,
        admin=admin_obj, candidate=candidate_obj, paper=paper_obj,
        schedule_time=s.schedule_time, duration_minutes=s.duration_minutes,
        max_questions=s.max_questions, start_time=s.start_time, end_time=s.end_time,
        status=s.status.value, total_score=s.total_score,
        current_status=s.current_status.value if s.current_status else None,
        last_activity=s.last_activity, warning_count=s.warning_count,
        max_warnings=s.max_warnings, is_suspended=s.is_suspended,
        suspension_reason=s.suspension_reason, suspended_at=s.suspended_at,
        enrollment_audio_path=s.enrollment_audio_path,
        candidate_name=s.candidate_name, admin_name=s.admin_name,
        is_completed=s.is_completed
    )
    
    # 5. Answers
    answers_nested = []
    for ans in s.result.answers:
        q_nested = None
        if ans.question:
            q_nested = QuestionNested(
                id=ans.question.id, content=ans.question.content,
                question_text=ans.question.question_text, topic=ans.question.topic,
                difficulty=ans.question.difficulty, marks=ans.question.marks,
                response_type=ans.question.response_type
            )
        
        answers_nested.append(AnswersNested(
            id=ans.id, interview_result_id=ans.interview_result_id,
            question=q_nested,
            candidate_answer=ans.candidate_answer, feedback=ans.feedback,
            score=ans.score, audio_path=ans.audio_path,
            transcribed_text=ans.transcribed_text, timestamp=ans.timestamp
        ))
        
    # 6. Top Level Result
    result_detail = InterviewResultDetail(
        id=s.result.id,
        interview=session_nested,
        interview_response=answers_nested,
        total_score=s.result.total_score,
        created_at=s.result.created_at
    )

    return ApiResponse(
        status_code=200,
        data=result_detail,
        message="Result details retrieved successfully"
    )

@router.patch("/results/{interview_id}", response_model=ApiResponse[DetailedResult])
async def update_result(
    interview_id: int,
    update_data: ResultUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update result scores and evaluations."""
    # Get the interview session
    interview_session = session.get(InterviewSession, interview_id)
    
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
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Update total score if provided
    if "total_score" in update_dict:
        interview_session.total_score = update_dict["total_score"]
    
    # Update individual responses if provided
    if "responses" in update_dict and update_dict["responses"]:
        for resp_update in update_dict["responses"]:
            response_id = resp_update.get("response_id")
            
            # Get the response
            answer = session.get(Answers, response_id)
            
            if not answer:
                raise HTTPException(
                    status_code=400,
                    detail=f"Response with ID {response_id} not found"
                )
            
            # Verify response belongs to this session
            # We need to query the result ID for this session
            if not interview_session.result:
                 # Should have a result if we are updating it? 
                 # Or maybe the result object is created on finish?
                 # If no result, we can't have answers.
                 raise HTTPException(status_code=400, detail="Interview has no result object")
                 
            if answer.interview_result_id != interview_session.result.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Response {response_id} does not belong to session {interview_id}"
                )
            
            # Update score if provided
            if "score" in resp_update and resp_update["score"] is not None:
                answer.score = resp_update["score"]
            
            # Update evaluation text (feedback) if provided
            if "evaluation_text" in resp_update and resp_update["evaluation_text"] is not None:
                answer.feedback = resp_update["evaluation_text"]
            
            session.add(answer)
    
    # Save changes
    session.add(interview_session)
    try:
        session.commit()
        session.refresh(interview_session)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update proctor settings: {str(e)}")
    
    # Return updated result using GET logic
    # Return updated result using GET logic
    updated_result = await get_result(interview_id, current_user, session)
    updated_result.message = "Result updated successfully"
    return updated_result

@router.delete("/results/{interview_id}", response_model=ApiResponse[dict])
async def delete_result(
    interview_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Delete all result data for an interview session (hard delete responses, keep session)."""
    interview_session = session.get(InterviewSession, interview_id)
    if not interview_session or interview_session.admin_id != current_user.id:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Hard delete responses to keep session history but clear results
    if interview_session.result:
        responses = interview_session.result.answers
        for r in responses:
            session.delete(r)
    
    interview_session.total_score = None
    session.add(interview_session)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset evaluation: {str(e)}")
    
    return ApiResponse(
        status_code=200,
        data={},
        message="Results deleted, interview session preserved"
    )

@router.get("/interviews/response/{response_id}")
async def get_response(response_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    """
    Get a specific response/answer details (for audio playback etc)
    """
    answer = session.get(Answers, response_id)
    if not answer:
       raise HTTPException(status_code=404, detail="Answer not found")
       
    # Authorization: Only admin who created the interview session associated with this answer
    if answer.interview_session.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this response")

    # We might need to construct a response that matches what UI expects if UI hasn't changed
    # Logic: return data
    return {
        "id": answer.id,
        "question_id": answer.question_id,
        "candidate_answer": answer.candidate_answer,
        "feedback": answer.feedback,
        "score": answer.score,
        "timestamp": answer.timestamp.isoformat() if answer.timestamp else None,
        "audio_path": answer.audio_path,
        "transcribed_text": answer.transcribed_text,
        "evaluation_text": answer.evaluation_text,
        "interview_id": answer.interview_id
    }

@router.get("/results/audio/{response_id}")
async def get_response_audio(
    response_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Streams a candidate's audio response for review."""
    response = session.get(Answers, response_id)
    if not response or not response.audio_path:
        raise HTTPException(status_code=404, detail="Audio response not found")
        
    # Answers -> InterviewResult -> InterviewSession
    if not response.interview_result or not response.interview_result.session or response.interview_result.session.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this audio")
        
    if not os.path.exists(response.audio_path):
        raise HTTPException(status_code=404, detail="Audio file missing on server")
        
    return FileResponse(
        response.audio_path,
        media_type="audio/wav",
        content_disposition_type="inline"
    )

@router.get("/interviews/enrollment-audio/{interview_id}")
async def get_enrollment_audio(
    interview_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Streams the candidate's enrollment audio for verification."""
    interview_session = session.get(InterviewSession, interview_id)
    if not interview_session or not interview_session.enrollment_audio_path:
        raise HTTPException(status_code=404, detail="Enrollment audio not found")
        
    if interview_session.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this audio")
        
    if not os.path.exists(interview_session.enrollment_audio_path):
        raise HTTPException(status_code=404, detail="Enrollment audio file missing on server")
        
    return FileResponse(
        interview_session.enrollment_audio_path,
        media_type="audio/wav",
        content_disposition_type="inline"
    )

# --- Identity & System ---



@router.post("/users", response_model=ApiResponse[UserRead])
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
    try:
        session.commit()
        session.refresh(new_user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
    
    return ApiResponse(
        status_code=201,
        data=UserRead(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value
        ),
        message="User created successfully"
    )

@router.get("/users", response_model=ApiResponse[List[UserRead]])
async def list_users(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    users = [UserRead(id=u.id, email=u.email, full_name=u.full_name, role=u.role.value) for u in session.exec(select(User)).all()]
    return ApiResponse(
        status_code=200,
        data=users,
        message="Users retrieved successfully"
    )

@router.get("/users/{user_id}", response_model=ApiResponse[UserDetailRead])
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
    
    return ApiResponse(
        status_code=200,
        data=UserDetailRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            resume_text=user.resume_text,
            has_profile_image=user.profile_image_bytes is not None,
            has_face_embedding=user.face_embedding is not None,
            created_interviews_count=len(created_interviews),
            participated_interviews_count=len(participated_interviews),
            profile_image_url=f"/api/candidate/profile-image/{user.id}" if user.profile_image_bytes or user.profile_image else None
        ),
        message="User details retrieved successfully"
    )

@router.patch("/users/{user_id}", response_model=ApiResponse[UserDetailRead])
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
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
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
                select(User).where(User.role == UserRole.SUPER_ADMIN)
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
    try:
        session.commit()
        session.refresh(user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
    
    # Return updated user details
    created_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all()
    participated_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all()
    
    return ApiResponse(
        status_code=200,
        data=UserDetailRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            resume_text=user.resume_text,
            has_profile_image=user.profile_image_bytes is not None,
            has_face_embedding=user.face_embedding is not None,
            created_interviews_count=len(created_interviews),
            participated_interviews_count=len(participated_interviews),
            profile_image_url=f"/api/candidate/profile-image/{user.id}" if user.profile_image_bytes or user.profile_image else None
        ),
        message="User updated successfully"
    )

@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Hard delete a user while preserving interview history by setting foreign keys to NULL."""
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
            select(User).where(User.role == UserRole.SUPER_ADMIN)
        ).all()
        
        if len(super_admin_count) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last Super Admin. Promote another user first."
            )
    
    # Preserve user info in related records before deletion
    # 1. Update interviews where user is admin
    admin_sessions = session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all()
    for interview in admin_sessions:
        interview.admin_name = user.full_name
        interview.admin_id = None
        session.add(interview)
    
    # 2. Update interviews where user is candidate
    candidate_sessions = session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all()
    for interview in candidate_sessions:
        interview.candidate_name = user.full_name
        interview.candidate_id = None
        session.add(interview)
    
    # 3. Update question papers where user is admin
    papers = session.exec(
        select(QuestionPaper).where(QuestionPaper.admin_id == user_id)
    ).all()
    for paper in papers:
        paper.admin_id = None
        session.add(paper)
    
    # Store info for response
    user_email = user.email
    user_name = user.full_name
    
    # Hard delete: user is permanently removed, but related data is preserved
    session.delete(user)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    
    return ApiResponse(
        status_code=200,
        data={
            "user_id": user_id,
            "email": user_email,
            "full_name": user_name,
            "interviews_preserved": len(admin_sessions) + len(candidate_sessions),
            "papers_preserved": len(papers)
        },
        message="User deleted successfully. Interview history and question papers preserved."
    )

@router.post("/shutdown", response_model=ApiResponse[dict])
def shutdown(current_user: User = Depends(get_admin_user)):
    """Graceful shutdown trigger."""
    if current_user.role != UserRole.SUPER_ADMIN: raise HTTPException(status_code=403)
    
    # Graceful shutdown for Uvicorn
    import signal
    os.kill(os.getpid(), signal.SIGTERM) # SIGTERM allows cleaning up
    return ApiResponse(
        status_code=200,
        data={},
        message="Server shutting down..."
    )

# --- Candidate Status Tracking ---


@router.get("/interviews/{interview_id}/status", response_model=ApiResponse[CandidateStatusResponse])
async def get_candidate_status(
    interview_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get comprehensive status tracking for a single interview candidate.
    
    Returns:
        - Full timeline of status changes
        - Warning count and violation details
        - Interview progress (questions answered/total)
        - Suspension status and reason
        - Last activity timestamp
    """
    from ..services.status_manager import get_status_summary
    
    # Get the interview session
    interview_session = session.exec(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.result).selectinload(InterviewResult.answers),
            selectinload(InterviewSession.selected_questions),
            selectinload(InterviewSession.proctoring_events)
        )
    ).first()
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview
    if interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this interview status"
        )
    
    # Generate comprehensive status summary
    status_data = get_status_summary(session, interview_session)
    
    return ApiResponse(
        status_code=200,
        data=CandidateStatusResponse(**status_data),
        message="Candidate status retrieved successfully"
    )

@router.get("/test-email")
async def test_email(
    background_tasks: BackgroundTasks,
    email: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    """Simple endpoint to test email configuration without scheduling an interview."""
    target_email = email or current_user.email
    subject = "AI Interview Platform - Diagnostic Test (Async)"
    link = f"{APP_BASE_URL}/admin/dashboard"
    
    logger.info(f"Queuing async test email for {target_email}")
    background_tasks.add_task(
        email_service.send_interview_invitation,
        to_email=target_email,
        candidate_name=current_user.full_name,
        link=link,
        time_str="Just Now (Diagnostic Async)",
        duration_minutes=0
    )
    
    return ApiResponse(
        status_code=200,
        data={"sent_to": target_email, "mode": "async"},
        message="Test email queued. Check server logs for delivery status."
    )

@router.get("/test-email-sync")
async def test_email_sync(
    email: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    """Synchronous version of test-email to see errors immediately in Swagger."""
    target_email = email or current_user.email
    link = f"{APP_BASE_URL}/admin/dashboard"
    
    logger.info(f"Sending SYNC test email for {target_email}")
    success = email_service.send_interview_invitation(
        to_email=target_email,
        candidate_name=current_user.full_name,
        link=link,
        time_str="Just Now (Diagnostic Sync)",
        duration_minutes=0
    )
    
    if success:
        return ApiResponse(
            status_code=200,
            data={"sent_to": target_email, "mode": "sync"},
            message="Test email sent successfully (Synchronous)."
        )
    else:
        raise HTTPException(
            status_code=500, 
            detail="Failed to send email synchronously. Check server logs for SMTP errors."
        )

