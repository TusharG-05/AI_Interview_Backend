"""
Status Manager Service - Centralized candidate status tracking and warning management.

This service handles:
- Status lifecycle transitions
- Warning accumulation and auto-suspension
- Violation categorization (soft vs hard)
- Status timeline recording
- WebSocket event broadcasting to candidates and admin dashboards
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlmodel import Session, select

from ..models.db_models import (
    User,
    InterviewSession, 
    StatusTimeline, 
    ProctoringEvent,
    CandidateStatus,
    InterviewStatus,
    Answers,
    InterviewResult
)
import json
import asyncio
import threading
from ..schemas.shared.user import serialize_user
from ..core.logger import get_logger
import asyncio

logger = get_logger(__name__)

# Database engine for ad-hoc queries
from datetime import date, timedelta

# ========== ASYNC WEBSOCKET HELPERS ==========

def get_enriched_admin_data(interview_id: int, session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Fetch comprehensive metadata for an interview session to enrich Admin WebSocket payloads.
    Includes candidate details, current status, and proctoring stats.
    """
    from ..core.database import engine
    
    # Internal helper to get metrics without opening a new session if one is already active
    def _get_metrics(db_session):
        try:
            # We don't want to open another session inside, so we'd ideally pass db_session
            # But compute_dashboard_metrics is currently self-contained. 
            # For now, we call it but we've at least fixed the NameError.
            return compute_dashboard_metrics()
        except Exception:
            return {"live": 0, "proctoring_activity": "0.00%", "failed_today": 0, "passed_today": 0}

    close_session = False
    if session is None:
        session = Session(engine)
        close_session = True
    
    try:
        # Fetch session with candidate details
        stmt = select(InterviewSession, User).join(User, InterviewSession.candidate_id == User.id).where(InterviewSession.id == interview_id)
        result = session.exec(stmt).first()
        
        if not result:
            logger.warning(f"Enrichment: Session {interview_id} or candidate not found")
            return {
                "interview_id": interview_id,
                "interview_status": "UNKNOWN",
                "candidate": {"candidate_id": None, "candidate_name": "Unknown", "candidate_email": "Unknown"},
                "proctoring_events": {"tab_switch_count": 0},
                "dashboard_data": _get_metrics(session)
            }
        
        interview_session, candidate = result
        
        return {
            "interview_id": interview_id,
            "interview_status": str(interview_session.status.value) if hasattr(interview_session.status, 'value') else str(interview_session.status),
            "candidate": {
                "candidate_id": candidate.id,
                "candidate_name": candidate.full_name,
                "candidate_email": candidate.email
            },
            "proctoring_events": {
                "tab_switch_count": interview_session.tab_switch_count,
                "warning_count": interview_session.warning_count,
                "max_warnings": interview_session.max_warnings
            },
            "dashboard_data": _get_metrics(session)
        }
    except Exception as e:
        logger.error(f"Error enriching admin data for {interview_id}: {e}", exc_info=True)
        return {
            "interview_id": interview_id,
            "interview_status": "ERROR",
            "candidate": {"candidate_id": None, "candidate_name": "Error", "candidate_email": str(e)},
            "proctoring_events": {"tab_switch_count": 0},
            "dashboard_data": {"live": 0, "proctoring_activity": "0.00%", "failed_today": 0, "passed_today": 0}
        }
    finally:
        if close_session:
            session.close()

async def _broadcast_violation_event(interview_id: int, event_type: str, details: Optional[str] = None):
    """
    Broadcast a violation event to both candidate and admin dashboard WebSockets.
    
    For candidates: Sends ViolationEvent immediately with warning counts
    For admin: Sends ViolationEvent with metadata
    """
    try:
        from .websocket_manager import manager
        from ..schemas.websocket.events import ViolationEvent
        
        # Broadcast to admin dashboard (include enriched data)
        # We do this first to get the most recent warning_count if needed
        enriched_data = get_enriched_admin_data(interview_id)
        
        # Extract counts from enriched data for the candidate payload
        warning_count = enriched_data.get("proctoring_events", {}).get("warning_count", 0)
        max_warnings = enriched_data.get("proctoring_events", {}).get("max_warnings", 3)

        # Map event_type to violation_type expected by ViolationEvent
        violation_type_map = {
            "tab_switch": "tab_switch",
            "MULTIPLE FACES DETECTED": "multiple_faces",
            "NO FACE DETECTED": "no_face",
            "SECURITY ALERT: UNAUTHORIZED PERSON": "wrong_candidate",
        }
        
        violation_type = violation_type_map.get(event_type, event_type.lower())
        
        # Create violation event for candidate
        violation_event = ViolationEvent(
            violation_type=violation_type,
            interview_id=interview_id,
            timestamp=datetime.now(timezone.utc),
            details=details,
            warning_count=warning_count,
            max_warnings=max_warnings
        )
        
        # Broadcast to candidate
        await manager.broadcast_to_candidate(
            interview_id,
            violation_event.model_dump(mode='json')
        )
        
        admin_payload = {
            "event_type": "violation_detected",
            "data": {
                **enriched_data,
                "violation_type": violation_event.violation_type,
                "details": violation_event.details,
                "timestamp": violation_event.timestamp.isoformat()
            }
        }

        # Broadcast to per-interview admin dashboards
        await manager.broadcast_to_admin_dashboard(
            interview_id,
            admin_payload
        )
        
        # Broadcast to global admin dashboards
        await manager.broadcast_to_admins(admin_payload)
        
        logger.debug(f"Violation event broadcast: {event_type} for interview {interview_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast violation event: {e}")


async def _broadcast_interview_suspended_event(interview_id: int, violation_type: str, tab_switch_count: int):
    """
    Broadcast interview suspension event to admin dashboard.
    Sent when violation threshold is exceeded.
    """
    try:
        from .websocket_manager import manager
        from ..schemas.websocket.events import AdminDashboardEvent
        
        # Create suspension event payload and include enriched data
        enriched_data = get_enriched_admin_data(interview_id)

        suspension_payload = {
            "event_type": "interview_suspended",
            "data": {
                **enriched_data,
                "reason": "max_warnings_exceeded",
                "warning_count": tab_switch_count,
                "max_warnings": tab_switch_count,
                "last_violation": violation_type,
                "suspension_metadata": {
                    "auto_suspended": True,
                    "suspended_at": datetime.now(timezone.utc).isoformat()
                }
            }
        }

        # Broadcast to per-interview admin dashboards
        await manager.broadcast_to_admin_dashboard(
            interview_id,
            suspension_payload
        )
        
        # Broadcast to global admin dashboards
        await manager.broadcast_to_admins(suspension_payload)
        
        logger.info(f"Interview suspension event broadcast for interview {interview_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast interview suspended event: {e}")


async def _broadcast_interview_started_event(interview_id: int):
    """Broadcast interview started event to admin dashboard."""
    try:
        from .websocket_manager import manager
        from ..schemas.websocket.events import AdminDashboardEvent
        
        # Create enriched payload
        enriched_data = get_enriched_admin_data(interview_id)

        payload = {
            "event_type": "interview_started",
            "data": {
                **enriched_data,
                "started_at": datetime.now(timezone.utc).isoformat()
            }
        }

        # Broadcast to per-interview admin dashboards
        await manager.broadcast_to_admin_dashboard(
            interview_id,
            payload
        )
        
        # Broadcast to global admin dashboards
        await manager.broadcast_to_admins(payload)
        
        logger.debug(f"Interview started event broadcast for interview {interview_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast interview started event: {e}")


async def _broadcast_interview_completed_event(interview_id: int, result_status: str):
    """Broadcast interview completed event to admin dashboard."""
    try:
        from .websocket_manager import manager
        from ..schemas.websocket.events import AdminDashboardEvent
        
        # Create enriched payload
        enriched_data = get_enriched_admin_data(interview_id)

        payload = {
            "event_type": "interview_completed",
            "data": {
                **enriched_data,
                "result_status": result_status,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }

        # Broadcast to per-interview admin dashboards
        await manager.broadcast_to_admin_dashboard(
            interview_id,
            payload
        )
        
        # Broadcast to global admin dashboards
        await manager.broadcast_to_admins(payload)
        
        logger.debug(f"Interview completed event broadcast for interview {interview_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast interview completed event: {e}")


async def _broadcast_interview_expired_event(interview_id: int):
    """Broadcast interview expired event to admin dashboard."""
    try:
        from .websocket_manager import manager
        from ..schemas.websocket.events import AdminDashboardEvent
        
        # Create enriched payload
        enriched_data = get_enriched_admin_data(interview_id)

        payload = {
            "event_type": "interview_expired",
            "data": {
                **enriched_data,
                "expired_at": datetime.now(timezone.utc).isoformat()
            }
        }

        # Broadcast to per-interview admin dashboards
        await manager.broadcast_to_admin_dashboard(
            interview_id,
            payload
        )
        
        # Broadcast to global admin dashboards
        await manager.broadcast_to_admins(payload)
        
        logger.debug(f"Interview expired event broadcast for interview {interview_id}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast interview expired event: {e}")
_main_loop: Optional[asyncio.AbstractEventLoop] = None

def set_main_loop(loop: asyncio.AbstractEventLoop):
    global _main_loop
    _main_loop = loop
    logger.debug("Main event loop registered in StatusManager.")

def _fire_async_broadcast(coro):
    """Fire and forget async broadcast (non-blocking)."""
    try:
        global _main_loop
        loop = None
        
        # 1. Try to get the running loop (works if called from main thread)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
            
        # 2. Use the registered main loop (works if called from background threads)
        if not loop:
            loop = _main_loop
            
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
        else:
            # Fallback for synchronous scripts or if loop is not yet running
            try:
                asyncio.run(coro)
            except RuntimeError:
                logger.debug("WS Broadcast: Could not find or run event loop, skipping broadcast.")
    except Exception as e:
        logger.error(f"Failed to fire async broadcast: {e}")

# Violation severity mapping
VIOLATION_SEVERITY = {
    # Soft violations - accumulate warnings
    "gaze_away": "warning",
    "brief_disconnect": "warning",
    "low_audio": "info",
    "connection_unstable": "info",
    
    # Hard violations - accumulate warnings
    "MULTIPLE FACES DETECTED": "warning",
    "NO FACE DETECTED": "info",
    "tab_switch": "warning",
    "SECURITY ALERT: UNAUTHORIZED PERSON": "info",
    "unauthorized_device": "info",
}


def record_status_change(
    session: Session,
    interview_session: InterviewSession,
    new_status: CandidateStatus,
    metadata: Optional[Dict[str, Any]] = None
) -> StatusTimeline:
    """
    Record a status change in the timeline and update session's current status.
    Broadcasts appropriate admin dashboard events for major status transitions.
    
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
    
    # Broadcast to Admin Dashboard for major status changes
    if new_status == CandidateStatus.INTERVIEW_COMPLETED:
        result_status = "Pass" if interview_session.result and interview_session.result.result_status == "PASS" else "Fail"
        _fire_async_broadcast(
            _broadcast_interview_completed_event(interview_session.id, result_status)
        )
    # Note: SUSPENDED events are broadcast in add_violation with more context
    # Note: INTERVIEW_EXPIRED is an InterviewStatus (session-level), not a CandidateStatus —
    #       expired broadcast is handled separately in the expiry cron/router.
    # START/LIVE transition should be handled by interview start logic
    
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
    Broadcasts violation events to both candidate and admin dashboard.
    
    Args:
        session: Database session
        interview_session: The interview session
        event_type: Type of violation (e.g., "gaze_away", "multiple_faces")
        details: Additional details about the violation
        force_severity: Override automatic severity determination
    
    Returns:
        The created ProctoringEvent
    """
    # If the session is already suspended, skip all processing and broadcasting.
    # We only process violations until the moment of suspension.
    if interview_session.is_suspended:
        return None

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
        interview_session.status = InterviewStatus.COMPLETED
        interview_session.is_completed = True
        interview_session.end_time = datetime.now(timezone.utc)
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
        
        # Trigger result calculation for the suspended session
        from ..core.tasks import run_background_task
        from ..tasks.interview_tasks import process_session_results_task
        run_background_task(process_session_results_task, interview_session.id)
    
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
            interview_session.status = InterviewStatus.COMPLETED
            interview_session.is_completed = True
            interview_session.end_time = datetime.now(timezone.utc)
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
            
            # Trigger result calculation for the suspended session
            from ..core.tasks import run_background_task
            from ..tasks.interview_tasks import process_session_results_task
            run_background_task(process_session_results_task, interview_session.id)
    
    session.add(event)
    session.add(interview_session)
    session.commit()
    session.refresh(event)
    
    # Broadcast violation event to candidate and admin
    _fire_async_broadcast(
        _broadcast_violation_event(
            interview_session.id,
            event_type,
            details
        )
    )
    
    # If suspension occurred due to warnings, also broadcast the suspension event
    if interview_session.is_suspended and event.triggered_warning and severity == "warning":
        _fire_async_broadcast(
            _broadcast_interview_suspended_event(
                interview_session.id,
                event_type,
                interview_session.warning_count
            )
        )
    
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
    interview_session.status = InterviewStatus.COMPLETED
    interview_session.is_completed = True
    interview_session.end_time = datetime.now(timezone.utc)
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
    
    logger.info(f"Session {interview_session.id} manually suspended and marked COMPLETED: {reason}")
    
    # Trigger result calculation for the suspended session
    from ..core.tasks import run_background_task
    from ..tasks.interview_tasks import process_session_results_task
    run_background_task(process_session_results_task, interview_session.id)
    
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


def compute_dashboard_metrics(target_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Compute aggregated dashboard metrics for admin payloads.

    Returns:
        { live: int,
          proctoring_activity: str (percentage),
          failed_today: int,
          passed_today: int }
    """
    try:
        from sqlmodel import Session, select
        from sqlalchemy import distinct
        from datetime import datetime, timezone
        from ..core.database import engine

        if target_date is None:
            now = datetime.now(timezone.utc)
            target_date = now.date()

        start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        with Session(engine) as session:
            # live count
            live_sessions = session.exec(
                select(InterviewSession).where(InterviewSession.status.in_([InterviewStatus.LIVE, InterviewStatus.CONNECTED, InterviewStatus.DISCONNECTED]))
            ).all()
            live_count = len(live_sessions)

            # interviews started today (by start_time)
            interviews_today = session.exec(
                select(InterviewSession).where(
                    InterviewSession.start_time >= start,
                    InterviewSession.start_time < end
                )
            ).all()
            interviews_today_count = len(interviews_today)

            # distinct interviews with violations today (only for interviews started today)
            today_interview_ids = [i.id for i in interviews_today]
            if today_interview_ids:
                violation_rows = session.exec(
                    select(distinct(ProctoringEvent.interview_id)).where(
                        ProctoringEvent.timestamp >= start,
                        ProctoringEvent.timestamp < end,
                        ProctoringEvent.interview_id.in_(today_interview_ids)
                    )
                ).all()
                violation_interview_ids = {r[0] if isinstance(r, tuple) else r for r in violation_rows}
                violations_today_count = len(violation_interview_ids)
            else:
                violations_today_count = 0

            # results completed today
            results_today = session.exec(
                select(InterviewResult).where(
                    InterviewResult.created_at >= start,
                    InterviewResult.created_at < end
                )
            ).all()
            passed = 0
            failed = 0
            for r in results_today:
                status = (r.result_status or "").upper()
                if status == "PASS":
                    passed += 1
                elif status == "FAIL":
                    failed += 1

            # proctoring activity percentage
            if interviews_today_count > 0:
                pct = (violations_today_count / float(interviews_today_count)) * 100.0
            else:
                pct = 0.0

            proctoring_activity = f"{pct:.2f}%"

            return {
                "live": live_count,
                "proctoring_activity": proctoring_activity,
                "failed_today": failed,
                "passed_today": passed,
            }
    except Exception as e:
        logger.error(f"Failed to compute dashboard metrics: {e}")
        return {"live": 0, "proctoring_activity": "0.00%", "failed_today": 0, "passed_today": 0}


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
        # broadcast_interview_update(session, interview_session)
        pass

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
                # Create enriched payload
                enriched_data = get_enriched_admin_data(interview_session.id, session=session)
                
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_to_admins({
                        "event_type": update_type,
                        "data": {
                            **enriched_data,
                            "summary": summary
                        }
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
