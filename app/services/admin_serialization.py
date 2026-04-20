from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json as _json

from ..models.db_models import (
    InterviewSession, 
    User, 
    QuestionPaper, 
    CodingQuestionPaper, 
    InterviewResult, 
    Answers, 
    CodingAnswers,
    Team
)
from ..schemas.admin.results import (
    GetInterviewResultResponse,
    AdminAnswerAnswerShort as AnswerShort,
    AdminQuestionWithAnswer as QuestionWithAnswer,
    AdminPaperNested as PaperNestedWithAdminId,
    AdminPaperNested as CodingPaperNestedWithAdmin,
    AdminProctoringEvent as ProctoringEventRead
)
from ..schemas.admin.users import UserRead
from ..schemas.shared.team import TeamReadBasic
from ..schemas.shared.user import UserNested

from ..schemas.admin.papers import GetPaperResponse

def _get_enum_value(obj: Any) -> str:
    """Helper to safely get string value from Enum or string."""
    if obj is None: return ""
    return str(obj.value if hasattr(obj, 'value') else obj)

def serialize_team_basic(team: Optional[Team]) -> Optional[TeamReadBasic]:
    if not team: return None
    return TeamReadBasic(
        id=team.id,
        name=team.name,
        description=team.description or "",
        created_at=team.created_at.isoformat() if hasattr(team, "created_at") and team.created_at else ""
    )

def serialize_user_nested(user: Optional[User]) -> Optional[Dict[str, Any]]:
    if not user: return None
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": _get_enum_value(user.role),
        "access_token": None, # Not returned in admin detail for security
        "profile_image": user.profile_image,
        "team": serialize_team_basic(user.team)
    }

def serialize_paper_nested(paper: Optional[QuestionPaper]) -> Optional[Dict[str, Any]]:
    if not paper: return None
    return {
        "id": paper.id,
        "name": paper.name,
        "description": paper.description or "",
        "question_count": paper.question_count or 0,
        "total_marks": float(paper.total_marks or 0),
        "created_at": paper.created_at,
        "team_id": None, # Populate if available in model
        "questions": None
    }

def serialize_coding_paper_nested(paper: Optional[CodingQuestionPaper]) -> Optional[Dict[str, Any]]:
    if not paper: return None
    return {
        "id": paper.id,
        "name": paper.name,
        "description": paper.description or "",
        "question_count": paper.question_count or 0,
        "total_marks": float(paper.total_marks or 0),
        "created_at": paper.created_at,
        "team_id": None,
        "questions": None
    }

def serialize_interview_admin_detail(session_obj: InterviewSession) -> Dict[str, Any]:
    """
    Refactored serialization for interview details.
    Moved from admin.py to reduce cognitive complexity.
    """
    
    # 1. Map Admin & Candidate
    admin_data = serialize_user_nested(session_obj.admin)
    candidate_data = serialize_user_nested(session_obj.candidate)

    # 2. Map Question Papers
    paper_data = serialize_paper_nested(session_obj.paper)
    coding_paper_data = serialize_coding_paper_nested(session_obj.coding_paper)

    # 4. Proctoring Event Summary
    max_warn = session_obj.max_warnings or 3
    proctoring_event = {
        "id": session_obj.id,
        "warning_count": session_obj.warning_count or 0,
        "max_warnings": max_warn,
        "is_suspended": bool(session_obj.is_suspended),
        "suspension_reason": session_obj.suspension_reason,
        "suspended_at": session_obj.suspended_at,
        "allow_copy_paste": bool(session_obj.allow_copy_paste),
        "allow_question_navigate": bool(session_obj.allow_question_navigate),
        "allow_proctoring": bool(session_obj.allow_proctoring)
    }
    if session_obj.proctoring_events:
        proctoring_event["id"] = session_obj.proctoring_events[0].id

    # 5. Result Summary
    res_status = "PENDING"
    ans_count = 0
    if session_obj.result:
        res_status = session_obj.result.result_status or "PENDING"
        ans_count = len(session_obj.result.answers) + (len(session_obj.result.coding_answers) if hasattr(session_obj.result, "coding_answers") else 0)

    return {
        "id": session_obj.id,
        "access_token": session_obj.access_token,
        "admin_user": admin_data,
        "candidate_user": candidate_data,
        "paper": paper_data,
        "coding_paper": coding_paper_data,
        "interview_round": _get_enum_value(session_obj.interview_round),
        "schedule_time": session_obj.schedule_time,
        "duration_minutes": session_obj.duration_minutes or 1440,
        "max_questions": session_obj.max_questions,
        "start_time": session_obj.start_time,
        "end_time": session_obj.end_time,
        "status": _get_enum_value(session_obj.status),
        "current_status": _get_enum_value(session_obj.current_status),
        "response_count": ans_count,
        "last_activity": session_obj.last_activity,
        "result_status": res_status,
        "max_marks": float((paper_data["total_marks"] if paper_data else 0) + (coding_paper_data["total_marks"] if coding_paper_data else 0)),
        "total_score": float(session_obj.total_score or 0.0),
        "enrollment_audio_path": session_obj.enrollment_audio_path,
        "enrollment_audio_url": f"/api/admin/interviews/enrollment-audio/{session_obj.id}" if session_obj.enrollment_audio_path else None,
        "is_completed": bool(session_obj.is_completed),
        "allow_proctoring": bool(session_obj.allow_proctoring),
        "proctoring_event": proctoring_event
    }
