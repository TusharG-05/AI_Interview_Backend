"""
Status Manager Service - Centralized candidate status tracking and warning management.

This service handles:
- Status lifecycle transitions
- Warning accumulation and auto-suspension
- Violation categorization (soft vs hard)
- Status timeline recording
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlmodel import Session, select

from ..models.db_models import (
    InterviewSession, 
    StatusTimeline, 
    ProctoringEvent,
    CandidateStatus,
    InterviewStatus,
    Answers,
    InterviewResult
)
import json
from ..schemas.shared.user import serialize_user
from ..core.logger import get_logger

logger = get_logger(__name__)

# Violation severity mapping
VIOLATION_SEVERITY = {
    # Soft violations - accumulate warnings
    "gaze_away": "warning",
    "brief_disconnect": "warning",
    "low_audio": "info",
    "connection_unstable": "info",
    
    # Hard violations - accumulate warnings
    "MULTIPLE FACES DETECTED": "warning",
    "NO FACE DETECTED": "warning",
    "tab_switch": "warning",
    "SECURITY ALERT: UNAUTHORIZED PERSON": "critical",
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
    
    # Update session current status — store as string since the column type is str
    interview_session.current_status = new_status.value
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
        details=details or "",
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


def complete_interview_session(
    session: Session,
    interview_session: InterviewSession,
    *,
    reason: str = "duration_timeout",
    current_status_label: str = "Completed",
) -> InterviewResult:
    """Mark an interview session as completed and preserve a terminal result state."""
    interview_session.end_time = datetime.now(timezone.utc)
    interview_session.is_completed = True
    interview_session.status = InterviewStatus.COMPLETED
    interview_session.current_status = current_status_label

    record_status_change(
        session=session,
        interview_session=interview_session,
        new_status=CandidateStatus.INTERVIEW_COMPLETED,
        metadata={"reason": reason, "auto_completed": True},
    )

    result_obj = interview_session.result
    if result_obj is None:
        result_obj = InterviewResult(interview_id=interview_session.id, result_status="COMPLETED")
        interview_session.result = result_obj
        session.add(result_obj)
    elif result_obj.result_status == "PENDING":
        result_obj.result_status = "COMPLETED"

    session.add(interview_session)
    session.add(result_obj)
    session.commit()
    session.refresh(interview_session)
    session.refresh(result_obj)

    try:
        from ..services.camera import CameraService

        CameraService().clear_session(interview_session.id)
    except Exception as e:
        logger.warning(f"Failed to clear proctoring cache for session {interview_session.id}: {e}")

    return result_obj


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


def _get_timeline_data(session: Session, interview_id: int) -> List[Dict[str, Any]]:
    """Helper to fetch and format timeline entries."""
    timeline_stmt = select(StatusTimeline).where(
        StatusTimeline.interview_id == interview_id
    ).order_by(StatusTimeline.timestamp)
    entries = session.exec(timeline_stmt).all()
    return [
        {
            "status": e.status.value if hasattr(e.status, 'value') else str(e.status),
            "timestamp": e.timestamp.isoformat(),
            "metadata": json.loads(e.context_data) if e.context_data else None
        }
        for e in entries
    ]


def _get_warning_data(session: Session, interview_id: int, current_count: int, max_warnings: int) -> Dict[str, Any]:
    """Helper to fetch violations and format warning summary."""
    violations_stmt = select(ProctoringEvent).where(
        ProctoringEvent.interview_id == interview_id,
        ProctoringEvent.triggered_warning == True
    ).order_by(ProctoringEvent.timestamp)
    violations = session.exec(violations_stmt).all()
    
    return {
        "total_warnings": current_count,
        "warnings_remaining": max(0, max_warnings - current_count),
        "max_warnings": max_warnings,
        "violations": [
            {
                "type": v.event_type,
                "severity": v.severity,
                "timestamp": v.timestamp.isoformat(),
                "details": v.details
            }
            for v in violations
        ]
    }


def _get_progress_data(interview_session: InterviewSession, result: Optional[InterviewResult]) -> Dict[str, Any]:
    """Helper to calculate interview progress and current question."""
    answered_questions = len(result.answers) if result else 0
    total_questions = len(interview_session.selected_questions) if interview_session.selected_questions else 0
    
    current_question_id = None
    if answered_questions < total_questions and interview_session.selected_questions:
        answered_ids = {r.question_id for r in result.answers} if result else set()
        for sq in sorted(interview_session.selected_questions, key=lambda x: x.sort_order):
            if sq.question_id not in answered_ids:
                current_question_id = sq.question_id
                break
                
    return {
        "questions_answered": answered_questions,
        "total_questions": total_questions,
        "current_question_id": current_question_id
    }


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
    # Check if result exists
    result_stmt = select(InterviewResult).where(InterviewResult.interview_id == interview_session.id)
    result = session.exec(result_stmt).first()
    
    # 1. Timeline
    timeline = _get_timeline_data(session, interview_session.id)
    
    # 2. Warnings
    max_warn = interview_session.max_warnings or 3
    current_warn = interview_session.warning_count or 0
    warnings = _get_warning_data(session, interview_session.id, current_warn, max_warn)
    
    # 3. Progress
    progress = _get_progress_data(interview_session, result)
    
    # 4. Serialize users
    candidate_dict = serialize_user(interview_session.candidate)
    admin_dict = serialize_user(interview_session.admin) if interview_session.admin else None
    
    return {
        "interview": {
            "id": interview_session.id,
            "access_token": interview_session.access_token,
            "paper_id": interview_session.paper_id,
            "schedule_time": interview_session.schedule_time.isoformat() if interview_session.schedule_time else None,
            "duration_minutes": interview_session.duration_minutes or 1440,
            "max_questions": interview_session.max_questions,
            "start_time": interview_session.start_time.isoformat() if interview_session.start_time else None,
            "end_time": interview_session.end_time.isoformat() if interview_session.end_time else None,
            "status": interview_session.status.value if hasattr(interview_session.status, 'value') else str(interview_session.status),
            "score": (result.total_score if result else interview_session.total_score) or 0.0,
            "current_status": interview_session.current_status,
            "last_activity": interview_session.last_activity.isoformat() if interview_session.last_activity else None,
            "warning_count": current_warn,
            "max_warnings": max_warn,
            "is_suspended": interview_session.is_suspended or False,
            "suspension_reason": interview_session.suspension_reason,
            "suspended_at": interview_session.suspended_at.isoformat() if interview_session.suspended_at else None,
            "enrollment_audio_path": interview_session.enrollment_audio_path,
            "is_completed": interview_session.is_completed or False,
            "allow_proctoring": interview_session.allow_proctoring,
            "allow_copy_paste": interview_session.allow_copy_paste,
            "allow_question_navigate": interview_session.allow_question_navigate,
            "tab_switch_count": interview_session.tab_switch_count,
            "tab_switch_timestamp": interview_session.tab_switch_timestamp.isoformat() if interview_session.tab_switch_timestamp else None,
            "tab_warning_active": interview_session.tab_warning_active
        },
        "admin_user": admin_dict,
        "candidate_user": candidate_dict,
        "current_status": interview_session.current_status,
        "timeline": timeline,
        "warnings": warnings,
        "progress": progress,
        "is_suspended": interview_session.is_suspended,
        "suspension_reason": interview_session.suspension_reason,
        "suspended_at": interview_session.suspended_at.isoformat() if interview_session.suspended_at else None,
        "last_activity": interview_session.last_activity.isoformat() if interview_session.last_activity else None
    }


def update_last_activity(
    session: Session,
    interview_session: InterviewSession,
    broadcast: bool = True
) -> None:
    """
    Update the last activity timestamp for a session.
    
    Args:
        session: Database session
        interview_session: The interview session
        broadcast: Whether to broadcast the update to admins
    """
    interview_session.last_activity = datetime.now(timezone.utc)
    session.add(interview_session)
    session.commit()
    
    if broadcast:
        broadcast_interview_update(session, interview_session)

def broadcast_interview_update(
    session: Session,
    interview_session: InterviewSession,
    update_type: str = "interview_update"
) -> None:
    """
    Gather full status summary and broadcast it to all connected admin dashboards.
    
    Args:
        session: Database session
        interview_session: The interview session
        update_type: The type of update event to send
    """
    # 1. Get summary
    try:
        summary = get_status_summary(session, interview_session)
        
        # 2. Broadcast via WebSocket
        from .websocket_manager import manager
        import asyncio
        
        # Determine current loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_to_admins({
                        "type": update_type,
                        "interview_id": interview_session.id,
                        "data": summary
                    }), 
                    loop
                )
            else:
                logger.warning(f"WS Broadcast: Event loop not running for interview {interview_session.id}")
        except RuntimeError:
            # Fallback for threads without an event loop
            logger.debug("WS Broadcast: No event loop in thread, skipping real-time update.")
            
    except Exception as e:
        logger.error(f"WS Broadcast Update Fail: {e}")
