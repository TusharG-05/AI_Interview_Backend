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

def serialize_user_read(user: Optional[User]) -> Optional[UserRead]:
    if not user: return None
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=_get_enum_value(user.role),
        profile_image=user.profile_image,
        team=serialize_team_basic(user.team)
    )

def serialize_interview_admin_detail(session_obj: InterviewSession) -> GetInterviewResultResponse:
    """
    Refactored serialization for interview details.
    Moved from admin.py to reduce cognitive complexity.
    """
    
    # 1. Map Admin & Candidate
    admin_data = serialize_user_read(session_obj.admin)
    candidate_data = serialize_user_read(session_obj.candidate)

    # 2. Map Standard Question Paper
    paper_data = None
    if session_obj.paper:
        # We don't serialize full questions here to keep the response light for list/detail
        # unless explicitly requested. The schema GetPaperResponse expects questions=None usually.
        paper_data = GetPaperResponse(
            id=session_obj.paper.id,
            name=session_obj.paper.name,
            description=session_obj.paper.description or "",
            adminUser=session_obj.paper.admin.full_name if session_obj.paper.admin else None,
            question_count=session_obj.paper.question_count or 0,
            total_marks=session_obj.paper.total_marks or 0,
            created_at=session_obj.paper.created_at,
            questions=None
        )

    # 3. Map Coding Question Paper
    coding_paper_data = None
    if session_obj.coding_paper:
        coding_paper_data = PaperNestedWithAdminId(
            id=session_obj.coding_paper.id,
            name=session_obj.coding_paper.name,
            description=session_obj.coding_paper.description or "",
            admin_user=session_obj.coding_paper.admin.id if session_obj.coding_paper.admin else None,
            question_count=session_obj.coding_paper.question_count or 0,
            total_marks=session_obj.coding_paper.total_marks or 0.0,
            created_at=session_obj.coding_paper.created_at,
            questions=None
        )

    # 4. Proctoring Event Summary
    max_warn = session_obj.max_warnings or 3
    proctoring_event = ProctoringEventRead(
        id=session_obj.id, # Use session ID as default identifier
        warning_count=session_obj.warning_count or 0,
        max_warnings=max_warn,
        is_suspended=session_obj.is_suspended or False,
        suspension_reason=session_obj.suspension_reason,
        suspended_at=session_obj.suspended_at,
        allow_copy_paste=session_obj.allow_copy_paste or False,
        allow_question_navigation=session_obj.allow_question_navigate or False
    )
    # If there are specific events, we could pull the ID from the first one
    if session_obj.proctoring_events:
        proctoring_event.id = session_obj.proctoring_events[0].id

    # 5. Result Summary
    res_status = "PENDING"
    ans_count = 0
    if session_obj.result:
        res_status = session_obj.result.result_status or "PENDING"
        ans_count = len(session_obj.result.answers) + len(session_obj.result.coding_answers)

    return GetInterviewResultResponse(
        id=session_obj.id,
        access_token=session_obj.access_token,
        admin_user=admin_data,
        candidate_user=candidate_data,
        paper=paper_data,
        coding_paper=coding_paper_data,
        interview_round=_get_enum_value(session_obj.interview_round),
        schedule_time=session_obj.schedule_time,
        duration_minutes=session_obj.duration_minutes or 1440,
        max_questions=session_obj.max_questions,
        start_time=session_obj.start_time,
        end_time=session_obj.end_time,
        status=_get_enum_value(session_obj.status),
        response_count=ans_count,
        last_activity=session_obj.last_activity,
        result_status=res_status,
        max_marks=(paper_data.total_marks if paper_data else 0) + (coding_paper_data.total_marks if coding_paper_data else 0),
        total_score=session_obj.total_score or 0.0,
        enrollment_audio_path=session_obj.enrollment_audio_path,
        enrollment_audio_url=f"/api/admin/interviews/enrollment-audio/{session_obj.id}" if session_obj.enrollment_audio_path else None,
        is_completed=session_obj.is_completed or False,
        proctoring_event=proctoring_event
    )
