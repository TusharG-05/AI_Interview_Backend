"""
Status Manager Service - Centralized candidate status tracking and warning management.

This service handles:
- Status lifecycle transitions
- Warning accumulation and auto-suspension
- Violation categorization (soft vs hard)
- Status timeline recording
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Session, select
from ..schemas.user_schemas import serialize_user
from ..models.db_models import (
    InterviewSession, 
    StatusTimeline, 
    ProctoringEvent,
    CandidateStatus,
    Answers,
    InterviewResult
)
import json
from ..core.logger import get_logger

logger = get_logger(__name__)

# Violation severity mapping
VIOLATION_SEVERITY = {
    # Soft violations - accumulate warnings
    "gaze_away": "warning",
    "brief_disconnect": "warning",
    "low_audio": "info",
    "connection_unstable": "info",
    
    # Hard violations - immediate suspension
    "multiple_faces": "critical",
    "tab_switch": "critical",
    "face_not_detected_extended": "critical",
    "unauthorized_device": "critical",
}


def record_status_change(
    session: Session,
    interview_session: InterviewSession,
    new_status: CandidateStatus,
    metadata: Optional[Dict[str, Any]] = None
) -> StatusTimeline:
    """
    Record a status change in the timeline and update session's current status.
    
    Args:
        session: Database session
        interview_session: The interview session to update
        new_status: The new status to transition to
        metadata: Optional additional context (stored as JSON)
    
    Returns:
        The created StatusTimeline entry
    """
    # Create timeline entry
    timeline_entry = StatusTimeline(
        interview_id=interview_session.id,
        status=new_status,
        timestamp=datetime.now(timezone.utc),
        context_data=json.dumps(metadata) if metadata else "{}"
    )
    
    # Update session current status
    interview_session.current_status = new_status
    interview_session.last_activity = datetime.now(timezone.utc)
    
    session.add(timeline_entry)
    session.add(interview_session)
    session.commit()
    session.refresh(timeline_entry)
    
    logger.info(
        f"Status change recorded for session {interview_session.id}: "
        f"{new_status.value} | Metadata: {metadata}"
    )
    
    # Broadcast to Admin Dashboard
    from .websocket_manager import manager
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_to_admins({
                    "type": "status_change",
                    "interview_id": interview_session.id,
                    "data": {
                        "status": new_status.value,
                        "metadata": metadata,
                        "timestamp": timeline_entry.timestamp.isoformat()
                    }
                }), 
                loop
            )
    except Exception as e:
        logger.error(f"WS Broadcast Fail: {e}")
    
    return timeline_entry


def add_violation(
    session: Session,
    interview_session: InterviewSession,
    event_type: str,
    details: Optional[str] = None,
    force_severity: Optional[str] = None
) -> ProctoringEvent:
    """
    Add a proctoring violation and potentially trigger warnings/suspension.
    
    Args:
        session: Database session
        interview_session: The interview session
        event_type: Type of violation (e.g., "gaze_away", "multiple_faces")
        details: Additional details about the violation
        force_severity: Override automatic severity determination
    
    Returns:
        The created ProctoringEvent
    """
    # Determine severity
    severity = force_severity or VIOLATION_SEVERITY.get(event_type, "info")
    
    # Create proctoring event
    event = ProctoringEvent(
        interview_id=interview_session.id,
        event_type=event_type,
        details=details,
        severity=severity,
        triggered_warning=False,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Handle critical violations - immediate suspension
    if severity == "critical":
        event.triggered_warning = True
        interview_session.is_suspended = True
        interview_session.suspension_reason = f"Critical violation: {event_type}"
        interview_session.suspended_at = datetime.now(timezone.utc)
        
        # Record status change to SUSPENDED
        record_status_change(
            session=session,
            interview_session=interview_session,
            new_status=CandidateStatus.SUSPENDED,
            metadata={
                "reason": event_type,
                "details": details,
                "auto_suspended": True
            }
        )
        
        logger.warning(
            f"Session {interview_session.id} SUSPENDED due to critical violation: {event_type}"
        )
    
    # Handle warning-level violations
    elif severity == "warning":
        interview_session.warning_count += 1
        event.triggered_warning = True
        
        logger.info(
            f"Warning added to session {interview_session.id}. "
            f"Count: {interview_session.warning_count}/{interview_session.max_warnings}"
        )
        
        # Check if warnings exceeded
        if interview_session.warning_count >= interview_session.max_warnings:
            interview_session.is_suspended = True
            interview_session.suspension_reason = f"Exceeded maximum warnings ({interview_session.max_warnings})"
            interview_session.suspended_at = datetime.now(timezone.utc)
            
            # Record status change to SUSPENDED
            record_status_change(
                session=session,
                interview_session=interview_session,
                new_status=CandidateStatus.SUSPENDED,
                metadata={
                    "reason": "max_warnings_exceeded",
                    "warning_count": interview_session.warning_count,
                    "last_violation": event_type
                }
            )
            
            logger.warning(
                f"Session {interview_session.id} AUTO-SUSPENDED: "
                f"Exceeded {interview_session.max_warnings} warnings"
            )
    
    session.add(event)
    session.add(interview_session)
    session.commit()
    session.refresh(event)
    
    # Broadcast to Admin Dashboard
    from .websocket_manager import manager
    import asyncio
    
    # Fire and forget (don't block the main thread)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_to_admins({
                    "type": "violation",
                    "interview_id": interview_session.id,
                    "data": {
                        "type": event_type,
                        "severity": severity,
                        "details": details,
                        "timestamp": event.timestamp.isoformat()
                    }
                }), 
                loop
            )
    except Exception as e:
        logger.error(f"WS Broadcast Fail: {e}")
    
    return event


def check_and_suspend(
    session: Session,
    interview_session: InterviewSession,
    reason: str
) -> bool:
    """
    Manually suspend an interview session.
    
    Args:
        session: Database session
        interview_session: The interview session to suspend
        reason: Reason for suspension
    
    Returns:
        True if suspended successfully, False if already suspended
    """
    if interview_session.is_suspended:
        logger.warning(f"Session {interview_session.id} is already suspended")
        return False
    
    interview_session.is_suspended = True
    interview_session.suspension_reason = reason
    interview_session.suspended_at = datetime.now(timezone.utc)
    
    record_status_change(
        session=session,
        interview_session=interview_session,
        new_status=CandidateStatus.SUSPENDED,
        metadata={"reason": reason, "manual_suspension": True}
    )
    
    session.add(interview_session)
    session.commit()
    
    logger.info(f"Session {interview_session.id} manually suspended: {reason}")
    return True


def get_status_summary(
    session: Session,
    interview_session: InterviewSession
) -> Dict[str, Any]:
    """
    Generate a comprehensive status summary for admin viewing.
    
    Args:
        session: Database session
        interview_session: The interview session
    
    Returns:
        Dictionary with timeline, warnings, progress, and current status
    """
    # Get timeline
    timeline_stmt = select(StatusTimeline).where(
        StatusTimeline.interview_id == interview_session.id
    ).order_by(StatusTimeline.timestamp)
    timeline_entries = session.exec(timeline_stmt).all()
    
    # Get violations
    violations_stmt = select(ProctoringEvent).where(
        ProctoringEvent.interview_id == interview_session.id,
        ProctoringEvent.triggered_warning == True
    ).order_by(ProctoringEvent.timestamp)
    violations = session.exec(violations_stmt).all()
    # Check implementation:
    # We need to find the InterviewResult for this session, then count answers
    # Or count Answers joined with InterviewResult where interview_id matches
    
    # Check if result exists
    result_stmt = select(InterviewResult).where(InterviewResult.interview_id == interview_session.id)
    result = session.exec(result_stmt).first()
    
    answered_questions = 0
    if result:
        # Count answers linked to this result
        # count() is not directly supported in all sqlmodel versions easily, using len of list or func.count
        # simpler: 
        answered_questions = len(result.answers)
    
    total_questions = len(interview_session.selected_questions) if interview_session.selected_questions else 0
    
    # Get current question (if any)
    current_question_id = None
    if answered_questions < total_questions and interview_session.selected_questions:
        # Next unanswered question
        if result and result.answers:
            answered_ids = {r.question_id for r in result.answers}
        else:
            answered_ids = set()
        for sq in sorted(interview_session.selected_questions, key=lambda x: x.sort_order):
            if sq.question_id not in answered_ids:
                current_question_id = sq.question_id
                break
    
    
    # Serialize candidate with role-based key
    candidate_dict = serialize_user(interview_session.candidate)
    
    return {
        "interview": {
            "id": interview_session.id,
            "access_token": interview_session.access_token,
            "admin_id": interview_session.admin_id,
            "candidate_id": interview_session.candidate_id,
            "paper_id": interview_session.paper_id,
            "schedule_time": interview_session.schedule_time.isoformat() if interview_session.schedule_time else None,
            "duration_minutes": interview_session.duration_minutes or 1440,
            "max_questions": interview_session.max_questions,
            "start_time": interview_session.start_time.isoformat() if interview_session.start_time else None,
            "end_time": interview_session.end_time.isoformat() if interview_session.end_time else None,
            "status": interview_session.status.value if hasattr(interview_session.status, 'value') else str(interview_session.status),
            "total_score": interview_session.total_score,
            "current_status": interview_session.current_status.value if interview_session.current_status else None,
            "last_activity": interview_session.last_activity.isoformat() if interview_session.last_activity else None,
            "warning_count": interview_session.warning_count or 0,
            "max_warnings": interview_session.max_warnings or 3,
            "is_suspended": interview_session.is_suspended or False,
            "suspension_reason": interview_session.suspension_reason,
            "suspended_at": interview_session.suspended_at.isoformat() if interview_session.suspended_at else None,
            "enrollment_audio_path": interview_session.enrollment_audio_path,
<<<<<<< HEAD
            "candidate_name": interview_session.candidate.full_name if interview_session.candidate else None,
            "admin_name": interview_session.admin.full_name if interview_session.admin else None,
            "is_completed": interview_session.is_completed
=======
            "candidate_name": interview_session.candidate.full_name if (interview_session.candidate and hasattr(interview_session.candidate, 'full_name')) else interview_session.candidate_name,
            "admin_name": interview_session.admin.full_name if (interview_session.admin and hasattr(interview_session.admin, 'full_name')) else interview_session.admin_name,
            "is_completed": interview_session.is_completed or False
>>>>>>> origin/main
        },
        "candidate": candidate_dict,
        "current_status": interview_session.current_status.value if interview_session.current_status else None,
        "timeline": [
            {
                "status": entry.status.value,
                "timestamp": entry.timestamp.isoformat(),
                "metadata": json.loads(entry.context_data) if entry.context_data else None
            }
            for entry in timeline_entries
        ],
        "warnings": {
            "total_warnings": interview_session.warning_count or 0,
            "warnings_remaining": max(0, (interview_session.max_warnings or 3) - (interview_session.warning_count or 0)),
            "max_warnings": interview_session.max_warnings or 3,
            "violations": [
                {
                    "type": v.event_type,
                    "severity": v.severity,
                    "timestamp": v.timestamp.isoformat(),
                    "details": v.details
                }
                for v in violations
            ]
        },
        "progress": {
            "questions_answered": answered_questions,
            "total_questions": total_questions,
            "current_question_id": current_question_id
        },
        "is_suspended": interview_session.is_suspended,
        "suspension_reason": interview_session.suspension_reason,
        "suspended_at": interview_session.suspended_at.isoformat() if interview_session.suspended_at else None,
        "last_activity": interview_session.last_activity.isoformat() if interview_session.last_activity else None
    }


def update_last_activity(
    session: Session,
    interview_session: InterviewSession
) -> None:
    """
    Update the last activity timestamp for a session.
    
    Args:
        session: Database session
        interview_session: The interview session
    """
    interview_session.last_activity = datetime.now(timezone.utc)
    session.add(interview_session)
    session.commit()
