from typing import List, Optional, Annotated
import json as _json
from datetime import datetime
from sqlalchemy import func
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, status, BackgroundTasks, Form, Header
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from ..core.database import get_db as get_session
from ..models.db_models import QuestionPaper, Questions, InterviewSession, Answers, CodingAnswers, InterviewResult, User, UserRole, ProctoringEvent, InterviewStatus, Team, InterviewRound, CodingQuestionPaper, CodingQuestions, CandidateStatus
from ..auth.dependencies import get_current_user_optional, get_admin_user
from ..auth.security import get_password_hash
from ..services.nlp import NLPService
from ..services.email import EmailService
from ..services.status_manager import record_status_change
from ..core.config import APP_BASE_URL, MAIL_USERNAME, MAIL_PASSWORD, FRONTEND_URL, CRON_SECRET
from ..core.logger import get_logger
from ..utils import calculate_average_score, format_iso_datetime
logger = get_logger(__name__)
from ..services.admin_serialization import serialize_interview_admin_detail
_serialize_interview_admin_detail = serialize_interview_admin_detail

from ..schemas.admin.users import CreateUserRequest, UserRead, GetUserDetailResponse
from ..schemas.admin.papers import GeneratePaperRequest, GetPaperResponse, CreatePaperRequest, UpdatePaperRequest, UpdateQuestionRequest, AdminQuestionRead, QuestionCreateData
from ..schemas.admin.interviews import ScheduleInterviewRequest, UpdateInterviewRequest, InterviewLinkResponse
from ..schemas.admin.results import GetInterviewResultResponse, UpdateResultRequest, AdminPaperNested as PaperNestedWithoutAdmin, AdminPaperNested as CodingPaperNestedWithoutAdmin, GetResultsResponse, InterviewSessionNested, GetAdminResultsListResponse
from ..schemas.shared.team import TeamReadBasic
from ..schemas.admin.coding import CodingQuestionFull, CodingPaperFull, GenerateCodingPaperRequest, CodingPaperCreateRequest, CodingPaperUpdateRequest, CodingQuestionCreateRequest, CodingQuestionUpdateRequest
from ..schemas.admin.dashboard import GetCandidateStatusResponse, LiveStatusItem, AdminInterviewSessionDetail,AdminInterviewsList
InterviewSessionDetail = AdminInterviewSessionDetail
from ..schemas.shared.api_response import ApiResponse
from ..schemas.shared.user import UserNested, serialize_user





import os
import shutil
import uuid
import secrets
from datetime import datetime, timedelta, timezone
import time

router = APIRouter(prefix="/admin", tags=["Admin"])

def create_response(api_response: ApiResponse):
    """Wrapper for ApiResponse to ensure forward compatibility with FastAPI response processing."""
    return api_response

nlp_service = NLPService()
email_service = EmailService()

# --- WebSocket Dashboard ---
from ..services.websocket_manager import manager
from fastapi import WebSocket, WebSocketDisconnect
from ..tasks.email_tasks import send_interview_invitation_task
from ..services.cloudinary_service import CloudinaryService

cloudinary_service = CloudinaryService()

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

@router.get("/papers", response_model=ApiResponse[List[GetPaperResponse]])
async def list_papers(
    current_user: Annotated[User, Depends(get_admin_user)],
    session: Annotated[Session, Depends(get_session)]
):
    """List all question papers created by the admin."""
    if current_user.role == UserRole.SUPER_ADMIN:
        stmt = select(QuestionPaper)
    else:
        stmt = select(QuestionPaper).where(QuestionPaper.admin_user == current_user.id)
    papers = session.exec(stmt).all()
    papers_data = [GetPaperResponse(
        id=p.id, name=p.name, description=p.description, 
        question_count=len(p.questions), 
        questions=[AdminQuestionRead(
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

class CreatePaperRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the question paper")
    description: Optional[str] = None



@router.post("/papers", response_model=ApiResponse[GetPaperResponse], status_code=201)
async def create_paper(
    paper_data: CreatePaperRequest,
    current_user: Annotated[User, Depends(get_admin_user)],
    session: Annotated[Session, Depends(get_session)]
):
    """Create a new collection of questions."""
    new_paper = QuestionPaper(
        name=paper_data.name,
        description=paper_data.description or "",
        admin_user=current_user.id
    )
    session.add(new_paper)
    try:
        session.commit()
        session.refresh(new_paper)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create paper: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create paper. Please try again.")
    paper_read = GetPaperResponse(
        id=new_paper.id, name=new_paper.name, description=new_paper.description, 
        question_count=0, questions=[], created_at=new_paper.created_at.isoformat(),
        created_by=serialize_user(current_user)
    )
    return ApiResponse(
        status_code=201,
        data=paper_read,
        message="Question paper created successfully"
    )

@router.post("/upload-doc", response_model=ApiResponse[dict])
async def upload_questions_doc(
    paper_id: int,
    current_user: Annotated[User, Depends(get_admin_user)],
    session: Annotated[Session, Depends(get_session)],
    file: UploadFile = File(...)
):
    """
    Upload a document (.pdf, .docx, .txt, .xlsx) to extract questions and add them to a paper.
    """
    import uuid
    import os
    # 1. Save file temporarily
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    temp_path = f"/tmp/{file_id}{ext}"
    
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    try:
        # 2. Extract questions
        extracted_data = nlp_service.extract_qa_from_file(temp_path, questions_only=True)
        
        if not extracted_data:
            return ApiResponse(
                status_code=400,
                message="No questions could be extracted from the document."
            )
            
        # 3. Add to paper
        paper = session.get(QuestionPaper, paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
            
        from ..models.db_models import Questions
        added_count = 0
        for item in extracted_data:
            q_text = item.get("question", "").strip()
            if not q_text: continue
            
            new_q = Questions(
                paper_id=paper_id,
                question_text=q_text,
                content=q_text,
                topic="Extracted",
                difficulty="Medium",
                marks=5,
                response_type="audio"
            )
            session.add(new_q)
            added_count += 1
            
        session.commit()
        
        return ApiResponse(
            status_code=200,
            data={"extracted_count": len(extracted_data), "added_to_paper": added_count},
            message=f"Successfully extracted and added {added_count} questions."
        )
        
    except Exception as e:
        logger.error(f"Error in upload_questions_doc: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/papers/{paper_id}", response_model=ApiResponse[GetPaperResponse])
async def get_paper(
    paper_id: int,
    current_user: Annotated[User, Depends(get_admin_user)],
    session: Annotated[Session, Depends(get_session)]
):
    """Get details of a specific question paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Super Admin can access everything; Admin only their own
    if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this paper")
    paper_read = GetPaperResponse(
        id=paper.id, name=paper.name, description=paper.description,
        question_count=len(paper.questions),
        questions=[AdminQuestionRead(
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

@router.patch("/papers/{paper_id}", response_model=ApiResponse[GetPaperResponse])
async def update_paper(
    paper_id:int,
    paper_update: UpdatePaperRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update a question paper's name or description."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this paper")
    
    update_data = paper_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is None and key in ["name", "description"]:
            value = ""
        setattr(paper, key, value)
    
    session.add(paper)
    try:
        session.commit()
        session.refresh(paper)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update paper {paper_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update paper. Please try again.")
    paper_read = GetPaperResponse(
        id=paper.id, name=paper.name, description=paper.description,
        question_count=len(paper.questions),
        questions=[AdminQuestionRead(
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
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this paper")
    
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
        logger.error(f"Failed to delete paper {paper_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete paper. Please try again.")
    return ApiResponse(
        status_code=200,
        data={},
        message="Paper and all associated questions deleted successfully"
    )


@router.post("/papers/{paper_id}/questions", response_model=ApiResponse[AdminQuestionRead], status_code=201)
async def add_question_to_paper(
    paper_id: int,
    q_data: QuestionCreateData,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """API for manually adding a new interview question to a paper."""
    paper = session.get(QuestionPaper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add questions to this paper")
        
    new_q = Questions(
        paper_id=paper_id,
        content=q_data.content or "",
        question_text=q_data.content or "",
        topic=q_data.topic or "General",
        difficulty=q_data.difficulty or "Medium",
        marks=q_data.marks or 1,
        response_type=q_data.response_type or "audio"
    )
    session.add(new_q)
    try:
        session.commit()
        session.refresh(new_q)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create question for paper {paper_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create question. Please try again.")
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
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view questions for this paper")
    questions = session.exec(select(Questions).where(Questions.paper_id == paper_id)).all()
    return ApiResponse(
        status_code=200,
        data=questions,
        message=f"Questions for paper '{paper.name}' retrieved successfully"
    )


# --- AI Question Paper Generation ---

@router.post("/generate-paper", response_model=ApiResponse[GetPaperResponse], status_code=201)
async def generate_paper(
    request_data: GeneratePaperRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """
    Generate a complete question paper using AI.

    Accepts an AI prompt (topic/job description), the expected years of experience,
    and the number of questions to generate. The LLM produces the questions and
    the resulting QuestionPaper is persisted in the database.
    """
    from ..services.interview import generate_questions_from_prompt

    # Call LLM
    try:
        generated_questions = generate_questions_from_prompt(
            ai_prompt=request_data.ai_prompt,
            years_of_experience=request_data.years_of_experience,
            num_questions=request_data.num_questions,
        )
    except ValueError as e:
        logger.error(f"AI service unavailable during paper generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="AI service is currently unavailable. Please try again later."
        )

    if not generated_questions:
        raise HTTPException(
            status_code=502,
            detail="AI returned no questions. Please try again."
        )

    # Build paper name
    paper_name = request_data.paper_name or (
        f"AI Generated: {request_data.ai_prompt[:50].strip()}"
        f" ({request_data.years_of_experience} yrs, {request_data.num_questions} Qs)"
    )

    # Create QuestionPaper
    new_paper = QuestionPaper(
        name=paper_name,
        description=(
            f"AI-generated paper. Topic: {request_data.ai_prompt}. "
            f"Experience: {request_data.years_of_experience} years. "
            f"Questions: {request_data.num_questions}."
        ),
        admin_user=current_user.id
    )
    session.add(new_paper)
    try:
        session.commit()
        session.refresh(new_paper)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create generated paper: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create paper for generated questions.")

    # Bulk-insert the generated questions
    question_objects = []
    total_marks = 0
    for q in generated_questions:
        question_text = q.get("question_text", "").strip()
        if not question_text:
            continue  # Skip malformed entries

        marks = int(q.get("marks", 5))
        total_marks += marks

        new_q = Questions(
            paper_id=new_paper.id,
            content=question_text,
            question_text=question_text,
            topic=q.get("topic", "General"),
            difficulty=q.get("difficulty", "Medium"),
            marks=marks,
            response_type=q.get("response_type", "text"),
        )
        session.add(new_q)
        question_objects.append(new_q)

    # Update counts on the paper
    new_paper.question_count = len(question_objects)
    new_paper.total_marks = total_marks
    session.add(new_paper)

    try:
        session.commit()
        session.refresh(new_paper)
        for q in question_objects:
            session.refresh(q)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save generated questions for paper {new_paper.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save generated questions. Please try again.")

    # Build response
    paper_read = GetPaperResponse(
        id=new_paper.id,
        name=new_paper.name,
        description=new_paper.description,
        question_count=new_paper.question_count,
        total_marks=new_paper.total_marks,
        questions=[
            AdminQuestionRead(
                id=q.id,
                content=q.content,
                question_text=q.question_text,
                topic=q.topic,
                difficulty=q.difficulty,
                marks=q.marks,
                response_type=q.response_type,
            )
            for q in question_objects
        ],
        created_at=new_paper.created_at.isoformat(),
        created_by=serialize_user(current_user)
    )

    return ApiResponse(
        status_code=201,
        data=paper_read,
        message=f"Question paper generated successfully with {len(question_objects)} questions",
    )


# --- AI Coding Question Paper Generation (LeetCode-style) ---

@router.post("/generate-coding-paper", response_model=ApiResponse[CodingPaperFull], status_code=201)
async def generate_coding_paper(
    request_data: GenerateCodingPaperRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
):
    """
    Generate LeetCode-style coding problems via AI and append them to an
    existing CodingQuestionPaper. Each problem is saved as a structured
    `CodingQuestions` row (title, problem_statement, examples, constraints,
    starter_code) — not a JSON blob.
    """
    from ..services.interview import generate_coding_questions_from_prompt
    import json as _json
    from ..schemas.admin.results import (
        GetInterviewResultResponse as AdminResultData,
        AdminAnswerAnswerShort as AnswerShort,
        AdminQuestionWithAnswer as QuestionWithAnswer,
        AdminPaperNested as PaperNestedWithAdminId,
        AdminPaperNested as CodingPaperNestedWithAdmin,
        AdminProctoringEvent as ProctoringEventRead
    )

    # Validate difficulty_mix
    valid_mixes = {"easy", "medium", "hard", "mixed"}
    difficulty_mix = request_data.difficulty_mix.lower().strip()
    if difficulty_mix not in valid_mixes:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid difficulty_mix '{difficulty_mix}'. Must be one of: {sorted(valid_mixes)}"
        )

    # Always auto-create new paper
    paper_name = request_data.paper_name or f"AI {request_data.ai_prompt[:20]}..."
    paper = CodingQuestionPaper(
        name=paper_name,
        description=f"AI Generated coding paper for: {request_data.ai_prompt[:100]}",
        admin_user=current_user.id
    )
    session.add(paper)
    session.commit()
    session.refresh(paper)

    # Generate problems via LLM
    try:
        generated_problems = generate_coding_questions_from_prompt(
            ai_prompt=request_data.ai_prompt,
            difficulty_mix=difficulty_mix,
            num_questions=request_data.num_questions,
        )
    except ValueError as e:
        logger.error(f"AI service unavailable during coding paper generation: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="AI service is currently unavailable. Please try again later.")

    if not generated_problems:
        raise HTTPException(status_code=502, detail="AI returned no problems. Please try again.")

    # Bulk-insert problems as CodingQuestions rows
    question_objects: list[CodingQuestions] = []
    added_marks = 0

    for prob in generated_problems:
        title = prob.get("title", "").strip()
        if not title:
            continue

        marks = int(prob.get("marks", 6))
        added_marks += marks

        new_q = CodingQuestions(
            paper_id=paper.id,
            title=title,
            problem_statement=prob.get("problem_statement", ""),
            examples=_json.dumps(prob.get("examples", []), ensure_ascii=False),
            constraints=_json.dumps(prob.get("constraints", []), ensure_ascii=False),
            starter_code=prob.get("starter_code", ""),
            topic=prob.get("topic", "Algorithms"),
            difficulty=prob.get("difficulty", "Medium"),
            marks=marks,
        )
        session.add(new_q)
        question_objects.append(new_q)

    # Update cumulative counts on the paper
    paper.question_count = (paper.question_count or 0) + len(question_objects)
    paper.total_marks = (paper.total_marks or 0) + added_marks
    session.add(paper)

    try:
        session.commit()
        session.refresh(paper)
        for q in question_objects:
            session.refresh(q)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save coding problems for paper {paper.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save coding problems. Please try again.")

    # Build response using all questions now in the paper
    all_questions = session.exec(
        select(CodingQuestions).where(CodingQuestions.paper_id == paper.id)
    ).all()

    paper_full = CodingPaperFull(
        id=paper.id,
        name=paper.name,
        description=paper.description or "",
        question_count=paper.question_count,
        total_marks=paper.total_marks,
        questions=[
            CodingQuestionFull(
                id=q.id,
                paper_id=q.paper_id,
                title=q.title,
                problem_statement=q.problem_statement,
                examples=q.examples,        # model_validator parses JSON string
                constraints=q.constraints,  # model_validator parses JSON string
                starter_code=q.starter_code or None,
                topic=q.topic,
                difficulty=q.difficulty,
                marks=q.marks,
            )
            for q in all_questions
        ],
        created_at=paper.created_at.isoformat(),
        created_by=serialize_user(current_user),
    )

    return ApiResponse(
        status_code=201,
        data=paper_full,
        message=f"Added {len(question_objects)} coding problems to '{paper.name}' (ID: {paper.id})",
    )



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
        logger.error(f"Failed to delete question {q_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete question. Please try again.")
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
    if current_user.role == UserRole.SUPER_ADMIN:
        stmt = select(Questions)
    else:
        stmt = (
            select(Questions)
            .join(QuestionPaper, isouter=True)
            .where((QuestionPaper.admin_user == current_user.id) | (Questions.paper_id == None))
        )
    questions = session.exec(stmt).all()
    return ApiResponse(
        status_code=200,
        data=questions,
        message="Questions retrieved successfully"
    )

@router.get("/questions/{q_id}", response_model=ApiResponse[AdminQuestionRead])
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
    if current_user.role != UserRole.SUPER_ADMIN and q.paper and q.paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this question")
    return ApiResponse(
        status_code=200,
        data=q,
        message="Question retrieved successfully"
    )

@router.patch("/questions/{q_id}", response_model=ApiResponse[AdminQuestionRead])
async def update_question(
    q_id: int,
    q_update: UpdateQuestionRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update specific fields of a question."""
    q = session.get(Questions, q_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    # Verify the question belongs to a paper owned by the admin (or is orphaned)
    if current_user.role != UserRole.SUPER_ADMIN and q.paper and q.paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this question")
    
    update_data = q_update.model_dump(exclude_unset=True)
    if "content" in update_data:
        q.question_text = update_data["content"] or "" 
        
    for key, value in update_data.items():
        if value is None:
            if key in ["content", "question_text", "topic"]:
                value = ""
            elif key == "difficulty":
                value = "Medium"
            elif key == "response_type":
                value = "audio"
            elif key == "marks":
                value = 1
        setattr(q, key, value)
    
    session.add(q)
    try:
        session.commit()
        session.refresh(q)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update question {q_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update question. Please try again.")
    return ApiResponse(
        status_code=200,
        data=q,
        message="Question updated successfully"
    )

# --- Interview Scheduling ---

@router.post("/interviews/schedule", response_model=ApiResponse[InterviewLinkResponse], status_code=201)
async def schedule_interview(
    schedule_data: ScheduleInterviewRequest, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user), 
    session: Session = Depends(get_session)
):
    """
    Schedule a new one-to-one interview and email the link.
    """
    # Validate Candidate & Get their Team
    candidate = session.get(User, schedule_data.candidate_id)
    if not candidate or candidate.role != UserRole.CANDIDATE:
         raise HTTPException(status_code=400, detail="Invalid Candidate ID")

    # Use team from request, and ensure candidate is associated
    team_id = schedule_data.team_id
    if team_id is not None:
        candidate.team_id = team_id
        session.add(candidate)

    # Validate Standard Paper (optional)
    paper = None
    if schedule_data.paper_id is not None:
        paper = session.get(QuestionPaper, schedule_data.paper_id)
        if not paper:
            raise HTTPException(status_code=400, detail="Invalid Question Paper ID")
        if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to use this question paper")

    # Validate Coding Paper (optional)
    coding_paper = None
    if schedule_data.coding_paper_id is not None:
        coding_paper = session.get(CodingQuestionPaper, schedule_data.coding_paper_id)
        if not coding_paper:
            raise HTTPException(status_code=400, detail="Invalid Coding Paper ID — paper not found")
        if current_user.role != UserRole.SUPER_ADMIN and coding_paper.admin_user != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to use this coding paper")

    # Access fields before any commits to prevent DetachedInstanceError in background tasks
    candidate_email = candidate.email.strip()
    candidate_full_name = candidate.full_name

    # Parse schedule time
    try:
        dt_str = schedule_data.schedule_time.replace("Z", "+00:00")
        schedule_dt = datetime.fromisoformat(dt_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid schedule_time format. ISO 8601 expected.")

    new_session = InterviewSession(
        admin_id=current_user.id,
        candidate_id=schedule_data.candidate_id,
        paper_id=schedule_data.paper_id,
        coding_paper_id=schedule_data.coding_paper_id,
        interview_round=schedule_data.interview_round,
        schedule_time=schedule_dt,
        duration_minutes=schedule_data.duration_minutes or 1440,
        max_questions=schedule_data.max_questions or 0,
        status=InterviewStatus.SCHEDULED,
        current_status=CandidateStatus.INVITED,
        last_activity=datetime.utcnow(),
        warning_count=0,
        max_warnings=3,
        is_suspended=False,
        is_completed=False,
        allow_copy_paste=schedule_data.allow_copy_paste,
        allow_question_navigate=schedule_data.allow_question_navigate
    )
    
    session.add(new_session)
    try:
        session.commit()
        session.refresh(new_session)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to schedule interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule interview. Please try again.")
    
    # Track initial status - INVITED
    from ..services.status_manager import record_status_change
    
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
    
    # Random Question Selection (Standard Paper only)
    import random
    from ..models.db_models import SessionQuestion

    if schedule_data.paper_id:
        # Get all questions from the standard paper
        available_questions = session.exec(
            select(Questions).where(Questions.paper_id == schedule_data.paper_id)
        ).all()

        if not available_questions:
            raise HTTPException(status_code=400, detail="Standard question paper has no questions")

        # Use all available questions (max_questions field kept for compatibility but not used)
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
            session.refresh(new_session)
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to assign questions to session {new_session.id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to assign questions to the interview.")
    # Coding paper is linked via FK on the session — no pre-assignment needed
    
    # Generate Link - Must match frontend route: /interview/:token
    link = f"{FRONTEND_URL}/interview-access?token={new_session.access_token}"
    # Send Email Invitation Asynchronously (prevent UI hang without Redis)
    try:
        background_tasks.add_task(
            email_service.send_interview_invitation,
            to_email=candidate_email, 
            candidate_name=candidate_full_name,
            link=link,
            time_str=format_iso_datetime(new_session.schedule_time),
            duration_minutes=new_session.duration_minutes
        )
    except Exception as cel_e:
        logger.error(f"Failed to queue email task: {cel_e}")
        warning = "Interview scheduled, but email invitation could not be queued."
    else:
        warning = "Email invitation queued for sending."
    
    # Serialize users with role-based keys
    admin_dict = serialize_user(current_user)  # {"admin": {...}}
    candidate_dict = serialize_user(candidate)  # {"candidate": {...}}
    
    
    interview_detail = InterviewSessionDetail(
        id=new_session.id,
        access_token=new_session.access_token,
        admin_id=new_session.admin_id,
        candidate_id=new_session.candidate_id,
        paper_id=new_session.paper_id,
        coding_paper_id=new_session.coding_paper_id,
        interview_round=new_session.interview_round.value if new_session.interview_round else None,
        schedule_time=format_iso_datetime(new_session.schedule_time),
        duration_minutes=new_session.duration_minutes,
        max_questions=new_session.max_questions,
        start_time=format_iso_datetime(new_session.start_time),
        end_time=format_iso_datetime(new_session.end_time),
        status=new_session.status.value,
        total_score=new_session.total_score,
        current_status=new_session.current_status or None,
        last_activity=format_iso_datetime(new_session.last_activity),
        warning_count=new_session.warning_count,
        max_warnings=new_session.max_warnings,
        is_suspended=new_session.is_suspended,
        suspension_reason=new_session.suspension_reason,
        suspended_at=format_iso_datetime(new_session.suspended_at),
        enrollment_audio_path=new_session.enrollment_audio_path,
        is_completed=new_session.is_completed or False,
        allow_copy_paste=new_session.allow_copy_paste,
        allow_question_navigate=new_session.allow_question_navigate,
        team_id=candidate.team_id,
        admin_user=admin_dict,
        candidate_user=candidate_dict
    )

    link_response = InterviewLinkResponse(
        interview=interview_detail,
        admin_user=admin_dict,
        candidate_user=candidate_dict,
        access_token=new_session.access_token,
        link=link,
        scheduled_at=format_iso_datetime(new_session.schedule_time),
        warning=warning
    )
    return ApiResponse(
        status_code=201,
        data=link_response,
        message="Interview scheduled successfully"
    )

@router.get("/interviews", response_model=ApiResponse[List[AdminInterviewsList]])
async def list_interviews(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """List interviews created by this admin."""
    # Super Admins see everything
    if current_user.role == UserRole.SUPER_ADMIN:
        sessions = session.exec(
            select(InterviewSession)
            .options(
                selectinload(InterviewSession.admin),
                selectinload(InterviewSession.candidate),
                selectinload(InterviewSession.result)
            )
        ).all()
    else:
        # Regular admins only see their own (or public) interviews
        sessions = session.exec(
            select(InterviewSession)
            .where(
                (InterviewSession.admin_id == current_user.id) | 
                (InterviewSession.admin_id == None)
            )
            .options(
                selectinload(InterviewSession.admin),
                selectinload(InterviewSession.candidate),
                selectinload(InterviewSession.result)
            )
        ).all()
    results = []
    for s in sessions:
        # Serialize users with role-based keys, handling NULL users
        #admin_dict = serialize_user(s.admin, fallback_role="admin")
        candidate_dict = serialize_user(s.candidate, fallback_role="candidate")

        results.append(AdminInterviewsList(
            id=s.id,
            candidate_user=candidate_dict,
            status=s.status.value,
            schedule_time=format_iso_datetime(s.schedule_time),
            total_score=(s.result.total_score if s.result else s.total_score) or 0.0,
            interview_round=s.interview_round.value if s.interview_round else None
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
    
    # Role-based visibility
    if current_user.role == UserRole.SUPER_ADMIN:
        stmt = select(InterviewSession).where(
            InterviewSession.status.in_([
                InterviewStatus.SCHEDULED,
                InterviewStatus.LIVE
            ])
        )
    else:
        stmt = select(InterviewSession).where(
            InterviewSession.admin_id == current_user.id,
            InterviewSession.status.in_([
                InterviewStatus.SCHEDULED,
                InterviewStatus.LIVE
            ])
        )
    
    stmt = stmt.options(
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
        
        # Serialize users
        candidate_dict = serialize_user(interview_session.candidate)
        admin_dict = serialize_user(interview_session.admin) if interview_session.admin else None
        
        # Serialize interview
        interview_dict = {
            "id": interview_session.id,
            "access_token": interview_session.access_token,
            "paper_id": interview_session.paper_id,
            "schedule_time": format_iso_datetime(interview_session.schedule_time),
            "duration_minutes": interview_session.duration_minutes,
            "max_questions": interview_session.max_questions,
            "start_time": format_iso_datetime(interview_session.start_time),
            "end_time": format_iso_datetime(interview_session.end_time),
            "status": interview_session.status.value,
            "total_score": (interview_session.result.total_score if interview_session.result else interview_session.total_score) or 0.0,
            "current_status": interview_session.current_status or None,
            "last_activity": format_iso_datetime(interview_session.last_activity),
            "warning_count": interview_session.warning_count,
            "max_warnings": interview_session.max_warnings,
            "is_suspended": interview_session.is_suspended,
            "suspension_reason": interview_session.suspension_reason,
            "suspended_at": format_iso_datetime(interview_session.suspended_at),
            "enrollment_audio_path": interview_session.enrollment_audio_path,
            "is_completed": interview_session.is_completed or False,
            "allow_copy_paste": interview_session.allow_copy_paste,
            "allow_question_navigate": interview_session.allow_question_navigate,
            "interview_round": interview_session.interview_round.value if interview_session.interview_round else None
        }
        
        results.append(LiveStatusItem(
            interview=interview_dict,
            admin_user=admin_dict,
            candidate_user=candidate_dict,
            current_status=interview_session.current_status or None,
            warning_count=interview_session.warning_count or 0,
            warnings_remaining=max(0, (interview_session.max_warnings or 3) - (interview_session.warning_count or 0)),
            is_suspended=interview_session.is_suspended or False,
            last_activity=format_iso_datetime(interview_session.last_activity),
            progress_percent=round(progress_percent, 1)
        ))
    
    return ApiResponse(
        status_code=200,
        data=results,
        message="Live interview status retrieved successfully"
    )


# The local _serialize_interview_admin_detail function has been replaced 
# by the dedicated service in app/services/admin_serialization.py

@router.get("/interviews/{interview_id}", response_model=ApiResponse[GetInterviewResultResponse])
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
            selectinload(InterviewSession.proctoring_events),
            selectinload(InterviewSession.paper).selectinload(QuestionPaper.admin),
            selectinload(InterviewSession.paper).selectinload(QuestionPaper.questions),
            selectinload(InterviewSession.coding_paper).selectinload(CodingQuestionPaper.questions)
        )
    ).first()
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if interview_session.admin_id and interview_session.admin_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to access this interview session"
        )
    
    try:
        data = _serialize_interview_admin_detail(interview_session)
        return ApiResponse(
            status_code=200,
            data=data,
            message="Interview details retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Serialization error in get_interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while preparing the interview details.")

@router.patch("/interviews/{interview_id}", response_model=ApiResponse[GetInterviewResultResponse])
async def update_interview(
    interview_id: int,
    update_data: UpdateInterviewRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update interview session details (schedule_time, duration, status, paper)."""
    # Retrieve the interview session
    interview_session = session.get(InterviewSession, interview_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin
    if current_user.role != UserRole.SUPER_ADMIN and interview_session.admin_id != current_user.id:
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
        if not paper:
            raise HTTPException(status_code=400, detail="Invalid Question Paper ID")
        if current_user.role != UserRole.SUPER_ADMIN and paper.admin_user != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to assign this paper")
    
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
        if value is None and key == "max_questions":
            value = 0
        setattr(interview_session, key, value)
    
    session.add(interview_session)
    try:
        session.commit()
        session.refresh(interview_session)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update interview {interview_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update interview. Please try again.")
    
    # Return updated interview details
    data = _serialize_interview_admin_detail(interview_session)
    return ApiResponse(
        status_code=200,
        data=data,
        message="Interview session updated successfully"
    )

@router.delete("/interviews/{interview_id}", response_model=ApiResponse[dict])
async def delete_interview(
    interview_id: int,
    current_user: Annotated[User, Depends(get_admin_user)],
    session: Annotated[Session, Depends(get_session)]
):
    """Hard delete an interview session and all related data (responses, proctoring events, etc.)."""
    # Retrieve the interview session with relationships loaded
    interview_session = session.exec(
        select(InterviewSession)
        .where(InterviewSession.id == interview_id)
        .options(
            selectinload(InterviewSession.result),
            selectinload(InterviewSession.proctoring_events),
            selectinload(InterviewSession.selected_questions),
            selectinload(InterviewSession.status_timeline),
            selectinload(InterviewSession.candidate)
        )
    ).first()
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: verify the session belongs to the requesting admin (handle NULL admin_id)
    if current_user.role != UserRole.SUPER_ADMIN and interview_session.admin_id and interview_session.admin_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this interview session"
        )
    
    # Store info for response before deletion
    candidate_name = interview_session.candidate.full_name if interview_session.candidate else "Unknown"
    scheduled_time = format_iso_datetime(interview_session.schedule_time)
    
    # Hard delete: this will cascade to responses, proctoring_events, selected_questions, status_timeline
    session.delete(interview_session)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete interview {interview_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete interview. Please try again.")
    
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

@router.get("/users/results", response_model=ApiResponse[List[GetAdminResultsListResponse]])
async def get_all_results(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    """API for the admin dashboard: Returns a flat list of candidate interview sessions and their results."""
    
    # 1. Join with InterviewResult to only show sessions that have a generated result.
    # This prevents 404 errors when viewing detailed results for scheduled/invited sessions.
    from ..models.db_models import InterviewResult
    if current_user.role == UserRole.SUPER_ADMIN:
        stmt = select(InterviewSession).join(InterviewResult)
    else:
        stmt = select(InterviewSession).join(InterviewResult).where(InterviewSession.admin_id == current_user.id)
        
    sessions = session.exec(
        stmt
        .options(
            selectinload(InterviewSession.candidate),
            selectinload(InterviewSession.admin),
            selectinload(InterviewSession.result)
        )
    ).all()
    
    results = []
    for s in sessions:
        res_status = "PENDING"
        total_score = 0.0
        if s.result:
            res_status = s.result.result_status or "PENDING"
            total_score = s.result.total_score or 0.0

        results.append(GetAdminResultsListResponse(
            id=s.id,
            admin_user=serialize_user(s.admin),
            candidate_user=serialize_user(s.candidate),
            status=s.status.value if hasattr(s.status, 'value') else str(s.status),
            result_status=res_status,
            end_time=s.end_time,
            total_score=total_score
        ))

    return ApiResponse(
        status_code=200,
        data=[result.model_dump(by_alias=True) for result in results],
        message="All interview results retrieved successfully"
    )


@router.get("/results/{interview_id}", response_model=ApiResponse[dict])
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
            selectinload(InterviewSession.candidate).selectinload(User.team),
            selectinload(InterviewSession.result).selectinload(InterviewResult.answers).selectinload(Answers.question),
            selectinload(InterviewSession.result).selectinload(InterviewResult.answers).selectinload(Answers.coding_question),
            selectinload(InterviewSession.result).selectinload(InterviewResult.coding_answers).selectinload(CodingAnswers.coding_question),
            selectinload(InterviewSession.admin).selectinload(User.team),
            selectinload(InterviewSession.paper).selectinload(QuestionPaper.questions),
            selectinload(InterviewSession.coding_paper).selectinload(CodingQuestionPaper.questions)
        )
    ).first()
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview OR super admin
    if interview_session.admin_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this result"
        )
        
    s = interview_session
    if not s.result:
         raise HTTPException(status_code=404, detail="Result not found for this interview")

    # Build nested objects according to new AdminResultData schema
    import json as _json
    from ..schemas.admin.results import (
        GetInterviewResultResponse as AdminResultData,
        AdminAnswerAnswerShort as AnswerShort,
        AdminQuestionWithAnswer as QuestionWithAnswer,
        CodingQuestionWithAnswer,
        AdminPaperNested as PaperNestedWithAdminId,
        AdminPaperNested as CodingPaperNestedWithAdmin,
        AdminProctoringEvent as ProctoringEventRead,
        InterviewSessionNested as InterviewSessionData
    )

    # Helper maps for answers lookup
    std_answers_map = {ans.question_id: ans for ans in s.result.answers if ans.question_id}
    coding_answers_map = {ans.coding_question_id: ans for ans in s.result.coding_answers if ans.coding_question_id}

    # 1. Admin
    admin_obj = None
    if s.admin:
        admin_obj = UserNested(
            id=s.admin.id, email=s.admin.email, full_name=s.admin.full_name, 
            role=s.admin.role.value if hasattr(s.admin.role, 'value') else str(s.admin.role),
            access_token=s.admin.access_token or "",
            team={"id": s.admin.team.id, "name": s.admin.team.name} if s.admin.team else None
        )
         
    # 2. Candidate
    candidate_obj = None
    if s.candidate:
        candidate_obj = UserNested(
            id=s.candidate.id, email=s.candidate.email, full_name=s.candidate.full_name,
            role=s.candidate.role.value if hasattr(s.candidate.role, 'value') else str(s.candidate.role),
            team={"id": s.candidate.team.id, "name": s.candidate.team.name} if hasattr(s.candidate, "team") and s.candidate.team else None
        )
        
    # 3. Paper (Standard) with Nested Answers
    paper_obj = None
    if s.paper:
        questions_with_answers = []
        for q in s.paper.questions:
            ans = std_answers_map.get(q.id)
            ans_short = None
            if ans:
                ans_short = AnswerShort(
                    id=ans.id,
                    interview_result_id=ans.interview_result_id,
                    candidate_answer=ans.candidate_answer or "",
                    feedback=ans.feedback or "",
                    score=ans.score or 0.0,
                    audio_path=ans.audio_path or "", 
                    transcribed_text=ans.transcribed_text or "",
                    timestamp=ans.timestamp or datetime.now(timezone.utc)
                )

            # Parsing coding_content if it's a proxy question in standard paper
            coding_content = None
            if q.response_type == "code" and q.content:
                try:
                    coding_content = _json.loads(q.content)
                except:
                    pass

            questions_with_answers.append(QuestionWithAnswer(
                id=q.id, paper_id=q.paper_id, content=q.content or "",
                question_text=q.question_text or q.content or "",
                topic=q.topic or "General", answer=ans_short,
                difficulty=str(q.difficulty), marks=q.marks or 0,
                response_type=str(q.response_type), coding_content=coding_content
            ))

        p_total = s.paper.total_marks if s.paper.total_marks else sum(q.marks or 0 for q in s.paper.questions)
        paper_obj = PaperNestedWithoutAdmin(
            id=s.paper.id, name=s.paper.name, description=s.paper.description or "",  
            question_count=len(questions_with_answers),
            questions=questions_with_answers,
            total_marks=p_total,
            created_at=s.paper.created_at,
            team_id=s.paper.admin.team_id if s.paper.admin else None
        )
        
    # 3.1 Coding Paper with Nested Answers
    coding_paper_obj = None
    if s.coding_paper:
        coding_questions_with_answers = []
        for q in s.coding_paper.questions:
            ans = coding_answers_map.get(q.id)
            ans_short = None
            if ans:
                ans_short = AnswerShort(
                    id=ans.id, interview_result_id=ans.interview_result_id,
                    candidate_answer=ans.candidate_answer or "",
                    feedback=ans.feedback or "", score=ans.score or 0.0,
                    audio_path=ans.audio_path or "",
                    transcribed_text=ans.transcribed_text or "",
                    timestamp=ans.timestamp or datetime.now(timezone.utc)
                )

            examples = q.examples
            if isinstance(examples, str):
                try: examples = _json.loads(examples)
                except: examples = []
            
            constraints = q.constraints
            if isinstance(constraints, str):
                try: constraints = _json.loads(constraints)
                except: constraints = []

            coding_questions_with_answers.append(CodingQuestionWithAnswer(
                id=q.id, paper_id=q.paper_id, title=q.title or "Coding Task",
                problem_statement=q.problem_statement or "",
                examples=examples or [], constraints=constraints or [],
                starter_code=q.starter_code or "", answer=ans_short,
                topic=q.topic or "Algorithms", difficulty=q.difficulty or "Medium",
                marks=q.marks or 0
            ))

        cp_total = s.coding_paper.total_marks if s.coding_paper.total_marks else sum(q.marks or 0 for q in s.coding_paper.questions)
        coding_paper_obj = CodingPaperNestedWithAdmin(
            id=s.coding_paper.id, name=s.coding_paper.name, description=s.coding_paper.description or "",
            admin_user=None,
            question_count=len(coding_questions_with_answers),
            total_marks=cp_total,
            created_at=s.coding_paper.created_at,
            questions=coding_questions_with_answers,
            team_id=s.coding_paper.admin.team_id if s.coding_paper.admin else None
        )
        
    # 4. Final Response Assembler
    response_count = (len(s.result.answers) if s.result else 0) + (len(s.result.coding_answers) if s.result else 0)
    max_marks = (paper_obj.total_marks if paper_obj else 0.0) + (coding_paper_obj.total_marks if coding_paper_obj else 0.0)
    
    proctoring = ProctoringEventRead(
        warning_count=s.warning_count or 0,
        max_warnings=s.max_warnings or 3,
        is_suspended=s.is_suspended or False,
        suspension_reason=s.suspension_reason,
        suspended_at=s.suspended_at,
        allow_copy_paste=s.allow_copy_paste or False,
        allow_question_navigation=s.allow_question_navigate or False
    )

    result_detail = AdminResultData(
        id=s.id, access_token=s.access_token, invite_link=None,
        admin_user=admin_obj, candidate_user=candidate_obj, 
        paper=paper_obj, coding_paper=coding_paper_obj,
        schedule_time=s.schedule_time, duration_minutes=s.duration_minutes,
        max_questions=s.max_questions, start_time=s.start_time, end_time=s.end_time,
        status=s.status.value if hasattr(s.status, 'value') else str(s.status).lower(),
        interview_round="Round 1", # Default value, can be updated later if needed
        response_count=response_count,
        last_activity=s.last_activity,
        result_status=s.result.result_status if s.result else "PENDING",
        max_marks=float(max_marks),
        total_score=float(s.result.total_score if s.result else 0.0),
        enrollment_audio_path=s.enrollment_audio_path,
        enrollment_audio_url=s.enrollment_audio_path, # Direct Cloudinary URL
        is_completed=s.is_completed or False,
        proctoring_event=proctoring
    )

    data_dict = result_detail.model_dump(exclude_none=True, by_alias=True)

    return ApiResponse(
        status_code=200,
        data=data_dict,
        message="Result details retrieved successfully"
    )

@router.patch("/results/{interview_id}", response_model=ApiResponse[dict])
async def update_result(
    interview_id: int,
    update_data: UpdateResultRequest,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update result scores and evaluations."""
    # Get the interview session
    interview_session = session.get(InterviewSession, interview_id)
    
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview OR super admin
    if interview_session.admin_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
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
        if interview_session.result:
            interview_session.result.total_score = update_dict["total_score"]
            
    # Update result status if provided
    if "result_status" in update_dict and interview_session.result:
        interview_session.result.result_status = update_dict["result_status"]
    
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
        logger.error(f"Failed to update result/responses for session {interview_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update result. Please try again.")
    
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
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Authorization: Only admin who created the interview OR super admin
    if interview_session.admin_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this result")
    
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
        logger.error(f"Failed to reset evaluation for session {interview_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reset evaluation.")
    
    return ApiResponse(
        status_code=200,
        data={},
        message="Results deleted, interview session preserved"
    )

@router.get("/interviews/response/{response_id}", response_model=ApiResponse[dict])
async def get_response(response_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    """
    Get a specific response/answer details (for audio playback etc)
    """
    # Load answer with result and session to avoid detached instance errors
    answer = session.exec(
        select(Answers)
        .where(Answers.id == response_id)
        .options(
            selectinload(Answers.interview_result).selectinload(InterviewResult.session)
        )
    ).first()

    if not answer:
       raise HTTPException(status_code=404, detail="Answer not found")
       
    # Authorization: Only admin who created the interview session OR super admin
    if answer.interview_result.session.admin_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this response")

    # We might need to construct a response that matches what UI expects if UI hasn't changed
    return ApiResponse(
        status_code=200,
        data={
            "id": answer.id,
            "question_id": answer.question_id,
            "candidate_answer": answer.candidate_answer,
            "feedback": answer.feedback,
            "score": answer.score,
            "timestamp": format_iso_datetime(answer.timestamp),
            "audio_path": answer.audio_path,
            "transcribed_text": answer.transcribed_text,
            "evaluation_text": getattr(answer, "feedback", None), # Map feedback to evaluation_text if needed by UI
            "interview_id": answer.interview_result.interview_id
        },
        message="Response details retrieved successfully"
    )

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
    # Authorization: Only admin who created the interview OR super admin
    # Relaxed: Allow if admin_id is None (unassigned)
    is_owner = response.interview_result.session.admin_id == current_user.id
    is_unassigned = response.interview_result.session.admin_id is None
    
    if not (is_owner or is_unassigned or current_user.role == UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to access this audio")
        
    if response.audio_path.startswith(("http://", "https://")):
        return RedirectResponse(url=response.audio_path)
        
    if not os.path.exists(response.audio_path):
        raise HTTPException(status_code=404, detail="Audio file missing on server")
        
    return FileResponse(
        response.audio_path,
        media_type="audio/wav", # Adjust if needed, but wav is standard for our recording uploads
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
        
    # Authorization: Only admin who created the interview OR super admin
    # Relaxed: Allow if admin_id is None (unassigned)
    is_owner = interview_session.admin_id == current_user.id
    is_unassigned = interview_session.admin_id is None

    if not (is_owner or is_unassigned or current_user.role == UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Not authorized to access this audio")
        
    if interview_session.enrollment_audio_path.startswith(("http://", "https://")):
        return RedirectResponse(url=interview_session.enrollment_audio_path)

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
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(UserRole.CANDIDATE),
    team_id: Optional[int] = Form(None),
    resume: Optional[UploadFile] = File(None),
    profile_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Create a new user with resume, profile picture, and face embeddings."""
    
    # Role-based creation logic
    if current_user.role == UserRole.ADMIN:
        if role != UserRole.CANDIDATE:
            raise HTTPException(
                status_code=403, 
                detail="Admins can only create candidates. For creating admins or super admins, please contact a super admin."
            )
    elif current_user.role == UserRole.SUPER_ADMIN:
        # Super Admin can create any role
        pass
    else:
        # Just in case some other role hits this
        raise HTTPException(status_code=403, detail="Operation not permitted")
    
    # 1. Existing user check
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Create initial user object
    new_user = User(
        email=email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        role=role,
        team_id=team_id
    )
    session.add(new_user)
    # We will commit everything at once at the end.
    
    updates_made = False

    # --- 3. Handle Profile Picture & Face Embeddings ---
    if profile_image:
        if profile_image.content_type and not (
            profile_image.content_type.startswith("image/") or 
            profile_image.content_type == "application/octet-stream"
        ):
            raise HTTPException(status_code=400, detail="Invalid image format")

        image_bytes = await profile_image.read()
        if image_bytes:
            new_user.profile_image_bytes = image_bytes
            
            # A. Generate Face Embeddings (Hybrid Strategy)
            try:
                from deepface import DeepFace
                import json
                import tempfile
                import os

                embeddings_map = {}
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                
                try:
                    # ArcFace
                    try:
                        arc_objs = DeepFace.represent(img_path=tmp_path, model_name="ArcFace", enforce_detection=False)
                        if arc_objs:
                            embeddings_map["ArcFace"] = arc_objs[0]["embedding"]
                    except Exception as e:
                        logger.warning(f"ArcFace failed during user creation: {e}")

                    # SFace
                    try:
                        sface_objs = DeepFace.represent(img_path=tmp_path, model_name="SFace", enforce_detection=False)
                        if sface_objs:
                            embeddings_map["SFace"] = sface_objs[0]["embedding"]
                    except Exception as e:
                        logger.warning(f"SFace failed during user creation: {e}")

                    if embeddings_map:
                        new_user.face_embedding = json.dumps(embeddings_map)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")

            # B. Upload to Cloudinary
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        cloudinary_service.upload_image, 
                        image_bytes, 
                        folder="profile_pictures" 
                    )
                    cloudinary_url = future.result(timeout=15)
                    if cloudinary_url:
                        new_user.profile_image = cloudinary_url
            except Exception as e:
                logger.error(f"Cloudinary upload failed: {e}")

    # --- 4. Handle Optional Resume Upload ---
    if resume:
        # Check if resume.filename is used instead of just 'filename'
        if not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        try:
            await resume.seek(0)
            # Upload to Cloudinary
            resume_url = cloudinary_service.upload_resume(resume.file, folder="resumes")
            if resume_url:
                new_user.resume_path = resume_url
                updates_made = True
            else:
                logger.error("Cloudinary upload returned None for resume")
        except Exception as e:
            logger.error(f"Failed to upload resume to Cloudinary: {e}")

    # 5. Final Save and refresh to get the ID
    try:
        session.commit()
        session.refresh(new_user)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to commit new user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create user.")
    
    # 6. Response
    team_data = None
    if new_user.team_id:
        from .teams import _serialize_team_basic
        team_data = _serialize_team_basic(new_user.team, session)

    return Response(
        content=ApiResponse(
            status_code=201,
            data=UserRead(
                id=new_user.id,
                email=new_user.email,
                full_name=new_user.full_name,
                role=new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role),
                resume_url=new_user.resume_path,
                profile_image=new_user.profile_image, 
                team=team_data
            ),
            message="User created with profile image and biometric embeddings."
        ).model_dump_json(),
        status_code=201,
        media_type="application/json"
    )

@router.get("/users", response_model=ApiResponse[List[UserRead]])
async def list_users(current_user: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    users_orm = session.exec(select(User)).all()
    from .teams import _serialize_team_basic
    
    users_data = []
    for u in users_orm:
        team_data = _serialize_team_basic(u.team, session) if u.team else None
        users_data.append(UserRead(
            id=u.id, 
            email=u.email, 
            full_name=u.full_name, 
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            resume_url=u.resume_path if u.resume_path else None,
            profile_image=u.profile_image,
            team=team_data
        ))
        
    return ApiResponse(
        status_code=200,
        data=users_data,
        message="Users retrieved successfully"
    )

@router.get("/users/{user_id}", response_model=ApiResponse[GetUserDetailResponse])
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
    
    from .teams import _serialize_team_basic
    team_data = _serialize_team_basic(user.team, session) if user.team else None

    return ApiResponse(
        status_code=200,
        data=GetUserDetailResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            has_profile_image=user.profile_image_bytes is not None,
            has_face_embedding=user.face_embedding is not None,
            created_interviews_count=len(created_interviews),
            participated_interviews_count=len(participated_interviews),
            resume_url=user.resume_path if user.resume_path else None,
            profile_image=user.profile_image,
            team=team_data
        ).model_dump(),
        message="User details retrieved successfully"
    )

@router.patch("/users/{user_id}", response_model=ApiResponse[GetUserDetailResponse])
async def update_user(
    user_id: int,
    email: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    team_id: Optional[int] = Form(None),
    resume: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """Update user details with optional resume replacement."""
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Email uniqueness
    if email and email != user.email:
        existing_user = session.exec(select(User).where(User.email == email)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = email
    
    if full_name:
        user.full_name = full_name
        
    if password:
        user.password_hash = get_password_hash(password)
        
    if team_id is not None:
        if team_id != 0:
            team = session.get(Team, team_id)
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            user.team_id = team_id
        else:
            user.team_id = None

    # Role change validation
    if role:
        try:
            new_role = UserRole(role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        if new_role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Unauthorized role promotion")
        
        if user.role == UserRole.SUPER_ADMIN and new_role != UserRole.SUPER_ADMIN:
            super_count = len(session.exec(select(User).where(User.role == UserRole.SUPER_ADMIN)).all())
            if super_count <= 1:
                raise HTTPException(status_code=400, detail="Last super admin protection")
        
        user.role = new_role

    # Handle optional resume upload
    if resume:
        if not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        try:
            await resume.seek(0)
            cloudinary_url = cloudinary_service.upload_resume(resume.file, folder="resumes")
            print(cloudinary_url)

            if cloudinary_url:
                user.resume_path = cloudinary_url
            else:
                logger.error("Cloudinary upload returned None for resume update")
                raise HTTPException(status_code=500, detail="Failed to upload resume to Cloudinary")
        except Exception as e:
            logger.error(f"Failed to update resume on Cloudinary: {e}")
            raise HTTPException(status_code=500, detail="Failed to save resume")

    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update user. Please try again.")
    
    # Return updated user details
    created_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all()
    participated_interviews = session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all()
    
    from .teams import _serialize_team_basic
    team_data = _serialize_team_basic(user.team, session) if user.team else None

    return create_response(ApiResponse(
        status_code=200,
        data=GetUserDetailResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            has_profile_image=user.profile_image_bytes is not None,
            has_face_embedding=user.face_embedding is not None,
            created_interviews_count=len(created_interviews),
            participated_interviews_count=len(participated_interviews),
            resume_url=user.resume_path if user.resume_path else None,
            profile_image=user.profile_image,
            team=team_data
        ),
        message="User updated successfully"
    ))

@router.get("/users/{user_id}/check-delete", response_model=ApiResponse[dict])
async def check_delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Pre-deletion dry-run check. Returns whether cascade-deleting this user
    will remove related data (interviews, question papers).
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    interviews_as_admin = len(session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all())
    interviews_as_candidate = len(session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all())
    question_papers = len(session.exec(
        select(QuestionPaper).where(QuestionPaper.admin_user == user_id)
    ).all())

    has_related_data = (interviews_as_admin + interviews_as_candidate + question_papers) > 0

    return ApiResponse(
        status_code=200,
        data={
            "user_id": user_id,
            "email": user.email,
            "role": user.role.value,
            "has_related_data": has_related_data,
            "related_data": {
                "interviews_as_admin": interviews_as_admin,
                "interviews_as_candidate": interviews_as_candidate,
                "question_papers": question_papers
            }
        },
        message="Pre-deletion check completed"
    )

@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Hard delete a user. All related interview sessions, results, answers,
    proctoring events, and question papers are cascade-deleted by the database.
    """
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
    
    # Collect counts for response before deletion
    interviews_as_admin = len(session.exec(
        select(InterviewSession).where(InterviewSession.admin_id == user_id)
    ).all())
    
    interviews_as_candidate = len(session.exec(
        select(InterviewSession).where(InterviewSession.candidate_id == user_id)
    ).all())
    
    papers_count = len(session.exec(
        select(QuestionPaper).where(QuestionPaper.admin_user == user_id)
    ).all())
    
    # Store info for response
    user_email = user.email
    user_name = user.full_name
    
    # Delete question papers owned by this user (cascade deletes their questions)
    papers = session.exec(
        select(QuestionPaper).where(QuestionPaper.admin_user == user_id)
    ).all()
    for paper in papers:
        session.delete(paper)

    # Hard delete: user is permanently removed
    # DB ON DELETE CASCADE handles InterviewSession → Result → Answers, etc.
    session.delete(user)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete user. Please try again.")
    
    return ApiResponse(
        status_code=200,
        data={
            "user_id": user_id,
            "email": user_email,
            "full_name": user_name,
            "interviews_deleted": interviews_as_admin + interviews_as_candidate,
            "papers_deleted": papers_count
        },
        message="User and all associated data deleted successfully."
    )

@router.post("/system/expire-interviews", response_model=ApiResponse[dict])
async def expire_interviews_manually(
    x_cron_secret: Optional[str] = Header(None, alias="X-CRON-SECRET"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    """
    Manually trigger interview expiration check.
    This endpoint can be called by external cron services for platforms that don't support background processes.
    
    For HF Spaces and Render free tier, set up a cron job to call this endpoint periodically.
    Example cron: */5 * * * * curl -X POST https://your-app.com/api/admin/system/expire-interviews -H "X-CRON-SECRET: $CRON_SECRET"
    """
    authorized = False

    if x_cron_secret and CRON_SECRET and x_cron_secret == CRON_SECRET:
        authorized = True

    if not authorized and current_user:
        if current_user.role == UserRole.SUPER_ADMIN:
            authorized = True

    if not authorized:
        raise HTTPException(status_code=403, detail="Unauthorized: invalid cron secret or admin token")
    
    from ..models.db_models import InterviewStatus
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    expired_count = 0
    
    # Find interviews that are scheduled/live and have expired
    candidate_sessions = session.exec(
        select(InterviewSession).where(
            InterviewSession.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.LIVE])
        )
    ).all()
    
    for interview_session in candidate_sessions:
        schedule_time = interview_session.schedule_time
        if schedule_time.tzinfo is None:
            schedule_time = schedule_time.replace(tzinfo=timezone.utc)
        
        expiration_time = schedule_time + timedelta(minutes=interview_session.duration_minutes)
        if now > expiration_time:
            interview_session.status = InterviewStatus.EXPIRED
            session.add(interview_session)
            expired_count += 1
    
    if expired_count > 0:
        session.commit()
    
    return ApiResponse(
        status_code=200,
        data={"expired_count": expired_count},
        message=f"Expiration check completed. {expired_count} interviews marked as expired."
    )

# --- Candidate Status Tracking ---


@router.get("/interviews/{interview_id}/status", response_model=ApiResponse[GetCandidateStatusResponse])
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
    
    # Authorization: Only admin who created the interview OR super admin
    if interview_session.admin_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this interview status"
        )
    
    # Generate comprehensive status summary
    status_data = get_status_summary(session, interview_session)
    
    return ApiResponse(
        status_code=200,
        data=GetCandidateStatusResponse(**status_data),
        message="Candidate status retrieved successfully"
    )

