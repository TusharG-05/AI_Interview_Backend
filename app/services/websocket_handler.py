"""
Candidate WebSocket event handlers.

Handles lifecycle and proctoring events sent by the candidate frontend.
All events go through `process_candidate_message` which dispatches to specific handlers.

Broadcasts to the global Admin Dashboard via `_broadcast_candidate_lifecycle`.
"""
import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket
from sqlmodel import Session, select

from ..models.db_models import (
    User, InterviewSession, CandidateStatus, InterviewStatus,
)
from ..core.logger import get_logger
from ..services.websocket_manager import manager
from ..services.status_manager import (
    add_violation,
    record_status_change,
    complete_interview_session,
    _broadcast_interview_started_event,
    _broadcast_interview_suspended_event,
    get_enriched_admin_data,
)

logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _norm_violation(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip().lower().replace("-", "_")


def log_info(interview_id: int, msg: str):
    logger.info(f"[Interview {interview_id}] {msg}")

def log_warning(interview_id: int, msg: str):
    logger.warning(f"[Interview {interview_id}] {msg}")

def log_error(interview_id: int, msg: str, exc_info: bool = False):
    logger.error(f"[Interview {interview_id}] {msg}", exc_info=exc_info)

def log_debug(interview_id: int, msg: str):
    logger.debug(f"[Interview {interview_id}] {msg}")


# Statuses where no further changes are allowed
TERMINAL_STATUSES = [
    InterviewStatus.COMPLETED,
    InterviewStatus.SUSPENDED,
    InterviewStatus.EXPIRED,
    InterviewStatus.CANCELLED,
]


# ──────────────────────────────────────────────────────────────────────────────
# Admin broadcast helper
# ──────────────────────────────────────────────────────────────────────────────

async def _broadcast_candidate_lifecycle(interview_id: int, event_type: str) -> None:
    """Broadcast a candidate lifecycle event to the global admin dashboard."""
    try:
        enriched_data = get_enriched_admin_data(interview_id)
        payload = {
            "event_type": event_type,
            "data": {
                **enriched_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        await manager.broadcast_to_admins(payload)
        log_debug(interview_id, f"Broadcast '{event_type}' to admin dashboard")
    except Exception as e:
        log_error(interview_id, f"Error broadcasting '{event_type}': {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Connection lifecycle
# ──────────────────────────────────────────────────────────────────────────────

async def handle_candidate_connect(interview_id: int, session: Session) -> None:
    """
    Called once after the WebSocket is accepted.
    Sets session status → CONNECTED and broadcasts Interview_login to admins.
    """
    try:
        log_info(interview_id, "Candidate WebSocket connected")

        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if session_obj and session_obj.status not in TERMINAL_STATUSES:
            old_status = session_obj.status
            session_obj.status = InterviewStatus.CONNECTED
            if old_status != session_obj.status:
                session.add(session_obj)
                session.commit()
                session.refresh(session_obj)
                log_info(interview_id, f"Status: {old_status} → CONNECTED")

        await _broadcast_candidate_lifecycle(interview_id, "Interview_login")
    except Exception as e:
        log_error(interview_id, f"handle_candidate_connect error: {e}")


async def handle_candidate_disconnect(interview_id: int) -> None:
    """
    Called when the WebSocket disconnects (cleanly or otherwise).
    Sets session status → DISCONNECTED and broadcasts Interview_disconnected.
    """
    try:
        manager.unregister_candidate(interview_id)
        log_info(interview_id, "Candidate WebSocket disconnected")

        from ..core.database import engine
        from sqlmodel import Session as DBSession

        with DBSession(engine) as s:
            session_obj = s.exec(
                select(InterviewSession).where(InterviewSession.id == interview_id)
            ).first()

            if session_obj and session_obj.status not in TERMINAL_STATUSES:
                old_status = session_obj.status
                session_obj.status = InterviewStatus.DISCONNECTED
                if old_status != session_obj.status:
                    s.add(session_obj)
                    s.commit()
                    log_info(interview_id, "Status: → DISCONNECTED")

        await _broadcast_candidate_lifecycle(interview_id, "Interview_disconnected")
    except Exception as e:
        log_error(interview_id, f"handle_candidate_disconnect error: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Message dispatcher
# ──────────────────────────────────────────────────────────────────────────────

async def process_candidate_message(
    interview_id: int, websocket: WebSocket, session: Session, data: dict
) -> None:
    """
    Dispatch incoming candidate messages to the appropriate handler.

    Expected message shapes (per new_websockets_plan.md):
        {"event_type": "Interview_login",        "Interview_status": "CONNECTED"}
        {"event_type": "Interview_started",      "Interview_status": "LIVE"}
        {"event_type": "Interview_disconnected", "Interview_status": "DISCONNECTED"}
        {"event_type": "Interview_finished",     "Interview_status": "COMPLETED"}
        {"event_type": "Interview_suspended",    "Interview_status": "SUSPENDED"}
        {"event_type": "Proctoring_violation",   "violation_type": "tab_switch"|"no_face"|...}
    """
    if not isinstance(data, dict):
        log_warning(interview_id, f"Non-dict message ignored: {data!r}")
        return

    event_type = (data.get("event_type") or "").strip().lower()

    # ── Proctoring violations ──────────────────────────────────────────────
    if event_type == "proctoring_violation":
        violation_type = _norm_violation(data.get("violation_type"))
        if violation_type == "tab_switch":
            await _handle_tab_switch(interview_id, session, data)
        else:
            await _handle_proctoring_violation(interview_id, session, data)
        return

    # ── Lifecycle events ───────────────────────────────────────────────────
    if event_type == "interview_login":
        await _handle_login(interview_id, session)
    elif event_type == "interview_started":
        await _handle_started(interview_id)
    elif event_type == "interview_finished":
        await _handle_finished(interview_id, session)
    elif event_type == "interview_disconnected":
        await _handle_disconnected(interview_id, session)
    elif event_type == "interview_suspended":
        await _handle_suspended(interview_id, session)
    else:
        log_debug(interview_id, f"Unhandled event_type={event_type!r}")


# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle handlers
# ──────────────────────────────────────────────────────────────────────────────

async def _handle_login(interview_id: int, session: Session) -> None:
    """Interview_login — re-broadcast in case of reconnection."""
    session_obj = session.exec(
        select(InterviewSession).where(InterviewSession.id == interview_id)
    ).first()

    if session_obj and session_obj.last_disconnected_at:
        now = datetime.now(timezone.utc)
        last_disconnect = session_obj.last_disconnected_at
        if last_disconnect.tzinfo is None:
            last_disconnect = last_disconnect.replace(tzinfo=timezone.utc)
        pause_duration = (now - last_disconnect).total_seconds()
        session_obj.paused_seconds += int(pause_duration)
        session_obj.last_disconnected_at = None
        session_obj.status = InterviewStatus.LIVE
        session.add(session_obj)

        from ..models.db_models import QuestionAttempt
        stmt = select(QuestionAttempt).where(
            QuestionAttempt.session_id == interview_id,
            QuestionAttempt.status == "active"
        )
        active_attempt = session.exec(stmt).first()
        if active_attempt and active_attempt.last_disconnected_at:
            att_last_disconnect = active_attempt.last_disconnected_at
            if att_last_disconnect.tzinfo is None:
                att_last_disconnect = att_last_disconnect.replace(tzinfo=timezone.utc)
            active_attempt.paused_seconds += int((now - att_last_disconnect).total_seconds())
            active_attempt.last_disconnected_at = None
            session.add(active_attempt)

        session.commit()
        log_info(interview_id, f"Added {int(pause_duration)} seconds to paused_seconds")

    await _broadcast_candidate_lifecycle(interview_id, "Interview_login")
    log_info(interview_id, "Interview_login processed")


async def _handle_started(interview_id: int) -> None:
    """
    Interview_started — set status LIVE, record start_time, broadcast.
    Uses its own DB session to avoid stale-session issues.
    """
    try:
        from ..core.database import engine
        from sqlmodel import Session as DBSession

        with DBSession(engine) as s:
            session_obj = s.get(InterviewSession, interview_id)
            if session_obj and session_obj.status not in TERMINAL_STATUSES:
                old = session_obj.status
                session_obj.status = InterviewStatus.LIVE
                if session_obj.start_time is None:
                    session_obj.start_time = datetime.now(timezone.utc)
                    log_info(interview_id, "start_time recorded")
                if old != session_obj.status:
                    s.add(session_obj)
                    s.commit()
                    log_info(interview_id, f"Status: {old} → LIVE")

        await _broadcast_interview_started_event(interview_id)
    except Exception as e:
        log_error(interview_id, f"_handle_started error: {e}", exc_info=True)


async def _handle_finished(interview_id: int, session: Session) -> None:
    """Interview_finished — complete session, trigger evaluation, broadcast."""
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if session_obj:
            complete_interview_session(
                session=session,
                interview_session=session_obj,
                reason="manual_finish",
                current_status_label="Completed",
            )
            from ..tasks.interview_tasks import process_session_results
            asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))

            try:
                from ..services.camera import CameraService
                CameraService().clear_session(interview_id)
            except Exception:
                pass

            log_info(interview_id, "Interview finished via WebSocket")
        else:
            log_warning(interview_id, "Interview_finished: session not found")
    except Exception as e:
        log_error(interview_id, f"_handle_finished error: {e}", exc_info=True)


async def _handle_disconnected(interview_id: int, session: Session) -> None:
    """Interview_disconnected — explicit frontend disconnect event or WS drop."""
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()
        
        if session_obj and session_obj.status not in TERMINAL_STATUSES:
            session_obj.status = InterviewStatus.DISCONNECTED
            session_obj.last_disconnected_at = datetime.now(timezone.utc)
            session.add(session_obj)
            
            from ..models.db_models import QuestionAttempt
            stmt = select(QuestionAttempt).where(
                QuestionAttempt.session_id == interview_id,
                QuestionAttempt.status == "active"
            )
            active_attempt = session.exec(stmt).first()
            if active_attempt:
                active_attempt.last_disconnected_at = session_obj.last_disconnected_at
                session.add(active_attempt)
                
            session.commit()
            log_info(interview_id, "WS Dropped/Disconnected. Status → DISCONNECTED")
            
        await _broadcast_candidate_lifecycle(interview_id, "Interview_disconnected")
        
    except Exception as e:
        log_error(interview_id, f"_handle_disconnected error: {e}", exc_info=True)


async def _handle_suspended(interview_id: int, session: Session) -> None:
    """
    Interview_suspended — frontend confirms max warnings exceeded.
    Backend already handles auto-suspension via add_violation; this is a
    belt-and-suspenders client confirmation.
    """
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if session_obj and not session_obj.is_suspended:
            now = datetime.now(timezone.utc)
            session_obj.is_suspended = True
            session_obj.status = InterviewStatus.SUSPENDED
            session_obj.is_completed = True
            session_obj.end_time = now
            session_obj.suspension_reason = "Client-initiated suspension"
            session_obj.suspended_at = now

            record_status_change(
                session=session,
                interview_session=session_obj,
                new_status=CandidateStatus.SUSPENDED,
                metadata={"reason": "client_initiated", "auto_suspended": False},
            )
            session.add(session_obj)
            session.commit()

            from ..services.status_manager import _fire_async_broadcast
            _fire_async_broadcast(
                _broadcast_interview_suspended_event(
                    interview_id, "client_initiated", session_obj.tab_switch_count
                )
            )
            log_info(interview_id, "Interview suspended via explicit frontend event")
        else:
            log_debug(interview_id, "Interview_suspended received but already suspended")
    except Exception as e:
        log_error(interview_id, f"_handle_suspended error: {e}", exc_info=True)


# ──────────────────────────────────────────────────────────────────────────────
# Proctoring handlers
# ──────────────────────────────────────────────────────────────────────────────

async def _handle_tab_switch(interview_id: int, session: Session, data: dict) -> None:
    """Handle Proctoring_violation with violation_type=tab_switch."""
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if not session_obj or session_obj.is_completed or session_obj.is_suspended:
            return

        now = datetime.now(timezone.utc)
        session_obj.tab_switch_count += 1
        session_obj.tab_switch_timestamp = now
        session_obj.tab_warning_active = True

        new_tab_switch_count = session_obj.tab_switch_count
        max_w = session_obj.max_warnings

        if new_tab_switch_count >= max_w:
            details = (
                f"Tab switch limit reached ({new_tab_switch_count}/{max_w}). "
                "Your interview is being suspended due to repeated tab switching."
            )
        elif new_tab_switch_count == max_w - 1:
            details = (
                f"Final warning ({new_tab_switch_count}/{max_w}): You switched tabs. "
                "One more tab switch will immediately suspend your interview."
            )
        else:
            remaining = max_w - new_tab_switch_count
            details = (
                f"Tab switch {new_tab_switch_count}/{max_w} detected. "
                f"Return to the interview page now. "
                f"{remaining} more tab switch(es) allowed before suspension."
            )

        add_violation(
            session=session,
            interview_session=session_obj,
            event_type="tab_switch",
            details=details,
            force_severity="warning",
        )

        if session_obj.is_suspended:
            from ..tasks.interview_tasks import process_session_results
            asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
            log_info(interview_id, "Suspended via tab_switch threshold — evaluation triggered")

        session.add(session_obj)
        session.commit()
        log_info(interview_id, f"tab_switch handled (count={session_obj.tab_switch_count})")
    except Exception as e:
        log_error(interview_id, f"_handle_tab_switch error: {e}", exc_info=True)


async def _handle_proctoring_violation(interview_id: int, session: Session, data: dict) -> None:
    """
    Handle Proctoring_violation events other than tab_switch.

    Accepted violation_type values:
        no_face | multiple_faces | gaze_away | mobile_phone | unauthorized_person
    """
    VIOLATION_TYPE_MAP = {
        "no_face":             "NO FACE DETECTED",
        "multiple_faces":      "MULTIPLE FACES DETECTED",
        "gaze_away":           "gaze_away",
        "mobile_phone":        "unauthorized_device",
        "unauthorized_person": "SECURITY ALERT: UNAUTHORIZED PERSON",
    }
    HUMAN_MESSAGES = {
        "no_face":             "No face detected. Please stay visible in front of the camera.",
        "multiple_faces":      "Multiple faces detected. Only you should be visible in the frame.",
        "gaze_away":           "Looking away detected. Please keep your eyes on the interview screen.",
        "mobile_phone":        "Mobile phone detected. Please remove any unauthorized devices.",
        "unauthorized_person": "Unrecognized face detected. Please ensure you are the registered candidate.",
    }

    try:
        raw_type = _norm_violation(data.get("violation_type", ""))
        event_type = VIOLATION_TYPE_MAP.get(raw_type)

        if not event_type:
            log_warning(
                interview_id,
                f"Unknown violation_type '{raw_type}'. "
                f"Accepted: {list(VIOLATION_TYPE_MAP.keys())}",
            )
            return

        details = HUMAN_MESSAGES.get(raw_type) or raw_type

        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if not session_obj:
            log_warning(interview_id, "proctoring_violation: session not found")
            return

        if session_obj.is_completed or session_obj.is_suspended:
            log_debug(interview_id, f"proctoring_violation ignored — session already ended")
            return

        add_violation(
            session=session,
            interview_session=session_obj,
            event_type=event_type,
            details=details,
        )

        if session_obj.is_suspended:
            from ..tasks.interview_tasks import process_session_results
            asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
            log_info(interview_id, f"Suspended via '{raw_type}' — evaluation triggered")

        session.add(session_obj)
        session.commit()
        log_info(
            interview_id,
            f"Proctoring violation '{raw_type}' handled "
            f"(warnings: {session_obj.warning_count}, tab switches: {session_obj.tab_switch_count}/{session_obj.max_warnings})",
        )
    except Exception as e:
        log_error(interview_id, f"_handle_proctoring_violation error: {e}", exc_info=True)
