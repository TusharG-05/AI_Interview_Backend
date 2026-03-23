"""
Router for managing dedicated CodingQuestionPaper and CodingQuestions resources.

All endpoints require admin authentication via the `get_admin_user` dependency.
Prefix: /admin/coding-papers
"""

from typing import List, Optional
import json as _json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..core.database import get_db as get_session
from ..models.db_models import CodingQuestionPaper, CodingQuestions, InterviewSession, User, Team
from ..auth.dependencies import get_admin_user
from ..schemas.shared.api_response import ApiResponse
from ..schemas.admin.coding import (
    CodingPaperFull, 
    CodingQuestionFull,
    CodingPaperCreateRequest as CodingPaperCreate,
    CodingPaperUpdateRequest as CodingPaperUpdate,
    CodingQuestionCreateRequest as CodingQuestionCreate,
    CodingQuestionUpdateRequest as CodingQuestionUpdate
)
from ..schemas.shared.user import serialize_user

from ..core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/coding-papers", tags=["Coding Papers"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_question_full(q: CodingQuestions) -> CodingQuestionFull:
    """Convert a CodingQuestions ORM row to its response schema."""
    return CodingQuestionFull(
        id=q.id,
        paper_id=q.paper_id,
        title=q.title,
        problem_statement=q.problem_statement,
        examples=q.examples,      # model_validator parses the JSON string
        constraints=q.constraints,
        starter_code=q.starter_code or None,
        topic=q.topic,
        difficulty=q.difficulty,
        marks=q.marks,
    )


def _build_paper_full(
    paper: CodingQuestionPaper,
    questions: List[CodingQuestions],
    admin_user: Optional[User] = None,
) -> CodingPaperFull:
    """Convert a CodingQuestionPaper ORM row to its response schema."""
    return CodingPaperFull(
        id=paper.id,
        name=paper.name,
        description=paper.description or "",
        question_count=paper.question_count,
        total_marks=paper.total_marks,
        questions=[_build_question_full(q) for q in questions],
        created_at=paper.created_at.isoformat(),
        created_by=serialize_user(admin_user) if admin_user else None,
    )


# ---------------------------------------------------------------------------
# Paper CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=ApiResponse[CodingPaperFull], status_code=201)
async def create_coding_paper(
    paper_data: CodingPaperCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[CodingPaperFull]:
    """Create a new coding question paper."""
    paper = CodingQuestionPaper(
        name=paper_data.name,
        description=paper_data.description or "",
        admin_user=current_user.id,
    )
    session.add(paper)
    try:
        session.commit()
        session.refresh(paper)
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to create coding paper: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create coding paper. Please try again.")

    return ApiResponse(
        status_code=201,
        data=_build_paper_full(paper, [], current_user),
        message="Coding paper created successfully",
    )


@router.get("/", response_model=ApiResponse[List[CodingPaperFull]])
async def list_coding_papers(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[List[CodingPaperFull]]:
    """List all coding papers owned by the current admin."""
    stmt = select(CodingQuestionPaper).where(CodingQuestionPaper.admin_user == current_user.id)
    papers = session.exec(stmt).all()

    result = []
    for p in papers:
        questions = session.exec(
            select(CodingQuestions).where(CodingQuestions.paper_id == p.id)
        ).all()
        result.append(_build_paper_full(p, questions, current_user))

    return ApiResponse(
        status_code=200,
        data=result,
        message=f"{len(result)} coding paper(s) retrieved",
    )


@router.get("/{paper_id}", response_model=ApiResponse[CodingPaperFull])
async def get_coding_paper(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[CodingPaperFull]:
    """Get a single coding paper with all its questions."""
    paper = session.get(CodingQuestionPaper, paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=404, detail="Coding paper not found")

    questions = session.exec(
        select(CodingQuestions).where(CodingQuestions.paper_id == paper_id)
    ).all()

    return ApiResponse(
        status_code=200,
        data=_build_paper_full(paper, questions, current_user),
        message="Coding paper retrieved successfully",
    )


@router.patch("/{paper_id}", response_model=ApiResponse[CodingPaperFull])
async def update_coding_paper(
    paper_id: int,
    update_data: CodingPaperUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[CodingPaperFull]:
    """Update a coding paper's name or description."""
    paper = session.get(CodingQuestionPaper, paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=404, detail="Coding paper not found")

    changes = update_data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(paper, key, value if value is not None else "")

    session.add(paper)
    try:
        session.commit()
        session.refresh(paper)
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to update coding paper {paper_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update coding paper. Please try again.")

    questions = session.exec(
        select(CodingQuestions).where(CodingQuestions.paper_id == paper_id)
    ).all()

    return ApiResponse(
        status_code=200,
        data=_build_paper_full(paper, questions, current_user),
        message="Coding paper updated successfully",
    )


@router.delete("/{paper_id}", response_model=ApiResponse[dict])
async def delete_coding_paper(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[dict]:
    """
    Delete a coding paper and all its questions.
    Fails if the paper is linked to any scheduled or live interview.
    """
    paper = session.get(CodingQuestionPaper, paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=404, detail="Coding paper not found")

    in_use = session.exec(
        select(InterviewSession).where(InterviewSession.coding_paper_id == paper_id)
    ).first()
    if in_use:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete this coding paper — it is linked to one or more interviews.",
        )

    session.delete(paper)
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to delete coding paper {paper_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete coding paper. Please try again.")

    return ApiResponse(
        status_code=200,
        data={},
        message="Coding paper and all its questions deleted successfully",
    )


# ---------------------------------------------------------------------------
# Question CRUD (nested under a paper)
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/questions", response_model=ApiResponse[CodingQuestionFull], status_code=201)
async def add_coding_question(
    paper_id: int,
    q_data: CodingQuestionCreate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[CodingQuestionFull]:
    """Add a new coding problem to an existing coding paper."""
    paper = session.get(CodingQuestionPaper, paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=404, detail="Coding paper not found")

    question = CodingQuestions(
        paper_id=paper_id,
        title=q_data.title,
        problem_statement=q_data.problem_statement,
        examples=_json.dumps(q_data.examples, ensure_ascii=False),
        constraints=_json.dumps(q_data.constraints, ensure_ascii=False),
        starter_code=q_data.starter_code or "",
        topic=q_data.topic,
        difficulty=q_data.difficulty,
        marks=q_data.marks,
    )
    session.add(question)

    # Update cumulative counts
    paper.question_count = (paper.question_count or 0) + 1
    paper.total_marks = (paper.total_marks or 0) + q_data.marks
    session.add(paper)

    try:
        session.commit()
        session.refresh(question)
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to add coding question to paper {paper_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add coding question. Please try again.")

    return ApiResponse(
        status_code=201,
        data=_build_question_full(question),
        message="Coding question added successfully",
    )


@router.get("/{paper_id}/questions", response_model=ApiResponse[List[CodingQuestionFull]])
async def list_coding_questions(
    paper_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[List[CodingQuestionFull]]:
    """List all questions belonging to a specific coding paper."""
    paper = session.get(CodingQuestionPaper, paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=404, detail="Coding paper not found")

    questions = session.exec(
        select(CodingQuestions).where(CodingQuestions.paper_id == paper_id)
    ).all()

    return ApiResponse(
        status_code=200,
        data=[_build_question_full(q) for q in questions],
        message=f"{len(questions)} question(s) retrieved",
    )


@router.patch("/questions/{q_id}", response_model=ApiResponse[CodingQuestionFull])
async def update_coding_question(
    q_id: int,
    q_update: CodingQuestionUpdate,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[CodingQuestionFull]:
    """Update specific fields of a coding question."""
    question = session.get(CodingQuestions, q_id)
    if not question:
        raise HTTPException(status_code=404, detail="Coding question not found")

    # Verify ownership via parent paper
    paper = session.get(CodingQuestionPaper, question.paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to update this question")

    old_marks = question.marks
    changes = q_update.model_dump(exclude_unset=True)

    for key, value in changes.items():
        if key == "examples":
            setattr(question, key, _json.dumps(value or [], ensure_ascii=False))
        elif key == "constraints":
            setattr(question, key, _json.dumps(value or [], ensure_ascii=False))
        else:
            setattr(question, key, value)

    # Keep paper totals in sync if marks changed
    if "marks" in changes and changes["marks"] != old_marks:
        diff = (changes["marks"] or 0) - old_marks
        paper.total_marks = (paper.total_marks or 0) + diff
        session.add(paper)

    session.add(question)
    try:
        session.commit()
        session.refresh(question)
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to update coding question {q_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update coding question. Please try again.")

    return ApiResponse(
        status_code=200,
        data=_build_question_full(question),
        message="Coding question updated successfully",
    )


@router.delete("/questions/{q_id}", response_model=ApiResponse[dict])
async def delete_coding_question(
    q_id: int,
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> ApiResponse[dict]:
    """Delete a coding question and update the parent paper's counts."""
    question = session.get(CodingQuestions, q_id)
    if not question:
        raise HTTPException(status_code=404, detail="Coding question not found")

    paper = session.get(CodingQuestionPaper, question.paper_id)
    if not paper or paper.admin_user != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to delete this question")

    # Update paper counters
    paper.question_count = max(0, (paper.question_count or 1) - 1)
    paper.total_marks = max(0, (paper.total_marks or question.marks) - question.marks)
    session.add(paper)

    session.delete(question)
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to delete coding question {q_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete coding question. Please try again.")

    return ApiResponse(
        status_code=200,
        data={},
        message="Coding question deleted successfully",
    )
