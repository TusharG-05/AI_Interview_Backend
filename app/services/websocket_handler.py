import time
import json
import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket, status
from sqlmodel import Session, select

from ..core.database import engine
from ..models.db_models import User, InterviewSession, CandidateStatus, InterviewStatus, UserRole
from ..core.logger import get_logger
from ..services.websocket_manager import manager
from ..services.status_manager import (
    add_violation, 
    record_status_change, 
    complete_interview_session,
    _broadcast_interview_started_event,
    _broadcast_interview_suspended_event,
    get_enriched_admin_data
)

logger = get_logger(__name__)


def _normalize_violation_type(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip().lower().replace("-", "_")

# Standardized logging helper
def log_info(interview_id: int, message: str):
    logger.info(f"[Interview ID: {interview_id}] {message}")

def log_warning(interview_id: int, message: str):
    logger.warning(f"[Interview ID: {interview_id}] {message}")

def log_error(interview_id: int, message: str, exc_info=False):
    logger.error(f"[Interview ID: {interview_id}] {message}", exc_info=exc_info)

def log_debug(interview_id: int, message: str):
    logger.debug(f"[Interview ID: {interview_id}] {message}")

# Terminal statuses — interviews in these states cannot be modified
TERMINAL_STATUSES = [
    InterviewStatus.COMPLETED,
    InterviewStatus.SUSPENDED,
    InterviewStatus.EXPIRED,
    InterviewStatus.CANCELLED,
]

# ========== CANDIDATE HANDLERS ==========

async def handle_candidate_connect(interview_id: int, websocket: WebSocket, session: Session):
    """Handle initial candidate connection and status update."""
    try:
        await manager.connect_candidate(websocket, interview_id)
        log_info(interview_id, "Candidate WebSocket connected")
        
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()
        
        if session_obj and session_obj.status not in TERMINAL_STATUSES:
            old_status = session_obj.status
            # On reconnection, we always move back to CONNECTED status.
            # This requires the candidate to explicitly "Start/Resume" to go LIVE.
            session_obj.status = InterviewStatus.CONNECTED
            
            if old_status != session_obj.status:
                session.add(session_obj)
                session.commit()
                session.refresh(session_obj)
                log_info(interview_id, f"Status updated: {old_status} -> {session_obj.status}")
        
        # Broadcast Interview_login to admin dashboard
        await _broadcast_candidate_lifecycle(interview_id, "Interview_login")
    except Exception as e:
        log_error(interview_id, f"Error in handle_candidate_connect: {e}")

async def handle_candidate_disconnect(interview_id: int, websocket: WebSocket):
    """Handle candidate disconnection and status update."""
    try:
        await manager.disconnect_candidate(websocket, interview_id)
        log_info(interview_id, "Candidate WebSocket disconnected")
        
        with Session(engine) as disconnect_session:
            session_obj = disconnect_session.exec(
                select(InterviewSession).where(InterviewSession.id == interview_id)
            ).first()
            
            if session_obj and session_obj.status not in TERMINAL_STATUSES:
                old_status = session_obj.status
                session_obj.status = InterviewStatus.DISCONNECTED
                
                if old_status != session_obj.status:
                    disconnect_session.add(session_obj)
                    disconnect_session.commit()
                    log_info(interview_id, "Status updated to DISCONNECTED")
        
        # Broadcast Interview_disconnected to admin dashboard
        await _broadcast_candidate_lifecycle(interview_id, "Interview_disconnected")
    except Exception as e:
        log_error(interview_id, f"Error in handle_candidate_disconnect: {e}")


async def _broadcast_candidate_lifecycle(interview_id: int, event_type: str):
    """Broadcast a candidate lifecycle event to the global admin dashboard."""
    try:
        enriched_data = get_enriched_admin_data(interview_id)
        payload = {
            "event_type": event_type,
            "data": {
                **enriched_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        await manager.broadcast_to_admins(payload)
        log_debug(interview_id, f"Broadcast {event_type} to admin dashboard")
    except Exception as e:
        log_error(interview_id, f"Error broadcasting {event_type}: {e}")


async def process_candidate_message(interview_id: int, websocket: WebSocket, session: Session, data: dict):
    """
    Dispatch candidate messages to specific handlers.
    
    All events use the 'event_type' field per spec:
    - Interview_login, Interview_started, Interview_disconnected, Interview_finished, Interview_suspended
    - Proctoring_violation (with violation_type sub-field)
    """
    if not isinstance(data, dict):
        log_warning(interview_id, f"Received non-dict message: {data}")
        return

    # Normalise event_type to lowercase for case-insensitive matching
    event_type = (data.get("event_type") or "").strip().lower()
    violation_type = _normalize_violation_type(data.get("violation_type"))

    # 1. Proctoring violation events
    #    Spec: {"event_type": "Proctoring_violation", "violation_type": "tab_switch" | "multiple_faces" | ...}
    if event_type in ("proctoring_violation", "violation_detected", "violation_messages"):
        if violation_type == "tab_switch":
            await handle_tab_switch_event(interview_id, session, data)
        else:
            await handle_proctoring_violation_event(interview_id, session, data)
        return

    # 2. Lifecycle events
    #    Spec: {"event_type": "Interview_login" | "Interview_started" | "Interview_finished" | ...}
    if event_type == "interview_login":
        await handle_login_event(interview_id, session, data)
    elif event_type == "interview_started":
        await handle_start_interview_event(interview_id, websocket, data)
    elif event_type == "interview_finished":
        await handle_finish_interview_event(interview_id, websocket, session, data)
    elif event_type == "interview_disconnected":
        await handle_explicit_disconnect_event(interview_id, websocket, session, data)
    elif event_type == "interview_suspended":
        await handle_explicit_suspend_event(interview_id, websocket, session, data)
    elif event_type == "face_verification":
        await handle_face_verification_frame(interview_id, session, data)
    else:
        log_debug(interview_id, f"Unhandled message: event_type={event_type!r}")

async def handle_face_verification_frame(interview_id: int, session: Session, data: dict):
    """
    Handle periodic face verification frame sent by frontend.
    Forwards the base64 image directly to Modal (ArcFace) for Identity matching.
    """
    image_b64 = data.get("image")
    if not image_b64:
        log_warning(interview_id, "face_verification missing 'image' data")
        return

    # Strip data URI scheme if present
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    try:
        import base64
        import cv2
        import numpy as np
        from sqlmodel import select
        from ..models.db_models import InterviewSession, User
        from ..services.face import FaceRecognizer

        img_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            log_warning(interview_id, "Failed to decode base64 face image")
            return

        session_obj = session.exec(select(InterviewSession).where(InterviewSession.id == interview_id)).first()
        if not session_obj:
            return
            
        candidate = session.exec(select(User).where(User.id == session_obj.candidate_id)).first()
        encoding_json = getattr(candidate, "face_embedding", None)
        
        if not encoding_json:
            log_warning(interview_id, "No enrolled face embedding for candidate. Skipping verification.")
            return

        recognizer = FaceRecognizer(known_encoding=encoding_json)
        
        # Frontend already sends the face crop, so we treat the entire image as the face box
        h, w = img_bgr.shape[:2]
        locs = [(0, w, h, 0)] # top, right, bottom, left
        
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        matches = recognizer.recognize(img_rgb, locs)
        
        is_authorized = any(matches) if matches else False
        
        if not is_authorized:
            log_warning(interview_id, "Face verification FAILED (Identity Mismatch).")
        else:
            log_info(interview_id, "Periodic face verification SUCCESS.")

    except Exception as e:
        log_error(interview_id, f"Error processing face verification frame: {e}")

async def handle_login_event(interview_id: int, session: Session, data: dict):
    """
    Handle Interview_login event.
    Spec: {"event_type": "Interview_login", "Interview_status": "CONNECTED"}
    """
    try:
        # Look up the candidate from the interview session
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()
        
        if session_obj:
            candidate = session.exec(
                select(User).where(User.id == session_obj.candidate_id)
            ).first()
            
            if candidate:
                log_info(interview_id, f"Candidate {candidate.email} login event processed")
            else:
                log_warning(interview_id, "Login event: Candidate not found in DB")
        else:
            log_warning(interview_id, "Login event: Session not found")
            
    except Exception as e:
        log_error(interview_id, f"Error processing login message: {e}", exc_info=True)

async def handle_tab_switch_event(interview_id: int, session: Session, data: dict):
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if session_obj and not session_obj.is_completed and not session_obj.is_suspended:
            now = datetime.now(timezone.utc)
            session_obj.tab_switch_count += 1
            session_obj.tab_switch_timestamp = now
            session_obj.tab_warning_active = True

            # Build a context-aware message.
            # At this point tab_switch_count is already incremented;
            # add_violation will also increment warning_count by 1.
            new_warning_count = session_obj.warning_count + 1
            max_w = session_obj.max_warnings

            if new_warning_count >= max_w:
                details_msg = (
                    f"Tab switch limit reached ({new_warning_count}/{max_w}). "
                    f"Your interview is being suspended due to repeated tab switching."
                )
            elif new_warning_count == max_w - 1:
                details_msg = (
                    f" Final warning ({new_warning_count}/{max_w}): You switched tabs. "
                    f"One more tab switch will immediately suspend your interview."
                )
            else:
                remaining = max_w - new_warning_count
                details_msg = (
                    f"Warning {new_warning_count}/{max_w}: You switched tabs. "
                    f"Return to the interview page now. "
                    f"{remaining} more tab switch(es) allowed before suspension."
                )

            add_violation(
                session=session,
                interview_session=session_obj,
                event_type="tab_switch",
                details=details_msg,
                force_severity="warning"
            )
            
            if session_obj.is_suspended:
                from ..tasks.interview_tasks import process_session_results
                asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
                log_info(interview_id, "Interview suspended via tab-switch threshold, triggering evaluation.")

            session.add(session_obj)
            session.commit()
            log_info(interview_id, f"Tab switch handled (Count: {session_obj.tab_switch_count})")
    except Exception as e:
        log_error(interview_id, f"Error processing tab_switch: {e}", exc_info=True)

async def handle_proctoring_violation_event(interview_id: int, session: Session, data: dict):
    """
    Handle a client-side proctoring violation sent by the frontend.

    Expected payload:
        {
            "event_type": "Proctoring_violation",
            "violation_type": "no_face" | "multiple_faces" | "gaze_away" | "mobile_phone" | "no_face",
        }
    """
    # Map frontend-friendly names → DB event_type strings used by add_violation / VIOLATION_SEVERITY
    VIOLATION_TYPE_MAP = {
        "no_face":            "NO FACE DETECTED",
        "multiple_faces":     "MULTIPLE FACES DETECTED",
        "gaze_away":          "gaze_away",
        "mobile_phone":       "unauthorized_device",
        "unauthorized_person": "SECURITY ALERT: UNAUTHORIZED PERSON",
    }

    # Human-readable messages for each violation type
    VIOLATION_HUMAN_MESSAGES = {
        "no_face":             "No face detected. Please stay visible in front of the camera.",
        "multiple_faces":      "Multiple faces detected. Only the candidate should be visible in the frame.",
        "gaze_away":           "Looking away from the screen detected. Please keep your eyes on the interview screen.",
        "mobile_phone":        "Mobile phone detected. Please remove any unauthorized devices.",
        "unauthorized_person": "Unrecognized face detected. Please ensure you are the registered candidate.",
    }

    try:
        raw_type = data.get("violation_type", "")
        event_type = VIOLATION_TYPE_MAP.get(raw_type)

        if not event_type:
            log_warning(
                interview_id,
                f"proctoring_violation: Unknown violation_type '{raw_type}'. "
                f"Accepted: {list(VIOLATION_TYPE_MAP.keys())}"
            )
            return

        # Use meaningful human-readable message; fall back to frontend-supplied details
        details = VIOLATION_HUMAN_MESSAGES.get(raw_type) or data.get("details") or raw_type

        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if not session_obj:
            log_warning(interview_id, f"proctoring_violation: Session not found")
            return

        if session_obj.is_completed or session_obj.is_suspended:
            log_debug(interview_id, f"proctoring_violation: Session already ended, ignoring '{raw_type}'")
            return

        add_violation(
            session=session,
            interview_session=session_obj,
            event_type=event_type,
            details=details,
            force_severity="warning"
        )

        # If the violation pushed over the threshold and suspended the session,
        # kick off result processing (same as tab_switch handler)
        if session_obj.is_suspended:
            from ..tasks.interview_tasks import process_session_results
            asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
            log_info(interview_id, f"Interview suspended via proctoring_violation '{raw_type}', triggering evaluation.")

        session.add(session_obj)
        session.commit()
        log_info(
            interview_id,
            f"Proctoring violation handled: '{raw_type}' "
            f"(warnings: {session_obj.warning_count}/{session_obj.max_warnings})"
        )
    except Exception as e:
        log_error(interview_id, f"Error processing proctoring_violation: {e}", exc_info=True)


async def handle_finish_interview_event(interview_id: int, websocket: WebSocket, session: Session, data: dict):
    """
    Handle Interview_finished event.
    Spec: {"event_type": "Interview_finished", "Interview_status": "COMPLETED"}
    """
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if session_obj:
            from ..tasks.interview_tasks import process_session_results
            from ..services.camera import CameraService

            complete_interview_session(
                session=session,
                interview_session=session_obj,
                reason="manual_finish",
                current_status_label="Completed",
            )
            
            asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
            
            try:
                CameraService().clear_session(interview_id)
            except Exception as cam_err:
                log_error(interview_id, f"Failed to clear camera session: {cam_err}")

            log_info(interview_id, "Interview finished via WebSocket")
        else:
            log_warning(interview_id, "Finish interview: Session not found")
    except Exception as e:
        log_error(interview_id, f"Error processing Interview_finished: {e}", exc_info=True)

async def handle_start_interview_event(interview_id: int, websocket: WebSocket, data: dict):
    """
    Handle Interview_started event.
    Spec: {"event_type": "Interview_started", "Interview_status": "LIVE"}
    """
    try:
        # Update database status to LIVE
        with Session(engine) as db_session:
            session_obj = db_session.get(InterviewSession, interview_id)
            if session_obj and session_obj.status not in TERMINAL_STATUSES:
                old_status = session_obj.status
                session_obj.status = InterviewStatus.LIVE
                
                # Only set start_time if it's the first time starting
                if session_obj.start_time is None:
                    session_obj.start_time = datetime.now(timezone.utc)
                    log_info(interview_id, "Initial start_time recorded")
                
                if old_status != session_obj.status:
                    db_session.add(session_obj)
                    db_session.commit()
                    log_info(interview_id, f"Status updated to LIVE via WebSocket (was {old_status})")

        await _broadcast_interview_started_event(interview_id)
        log_info(interview_id, "Interview start event triggered")
        
    except Exception as e:
        log_error(interview_id, f"Error processing Interview_started: {e}", exc_info=True)


async def handle_explicit_disconnect_event(interview_id: int, websocket: WebSocket, session: Session, data: dict):
    """
    Handle Interview_disconnected event sent explicitly by the frontend.
    Spec: {"event_type": "Interview_disconnected", "Interview_status": "DISCONNECTED"}
    """
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()
        
        if session_obj and session_obj.status not in TERMINAL_STATUSES:
            session_obj.status = InterviewStatus.DISCONNECTED
            session.add(session_obj)
            session.commit()
            log_info(interview_id, "Status updated to DISCONNECTED via explicit event")
        
        await _broadcast_candidate_lifecycle(interview_id, "Interview_disconnected")
    except Exception as e:
        log_error(interview_id, f"Error processing Interview_disconnected: {e}", exc_info=True)


async def handle_explicit_suspend_event(interview_id: int, websocket: WebSocket, session: Session, data: dict):
    """
    Handle Interview_suspended event sent by the frontend when max warnings exceeded.
    Spec: {"event_type": "Interview_suspended", "Interview_status": "SUSPENDED"}
    """
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()
        
        if session_obj and not session_obj.is_suspended:
            session_obj.is_suspended = True
            session_obj.status = InterviewStatus.SUSPENDED
            session_obj.is_completed = True
            session_obj.end_time = datetime.now(timezone.utc)
            session_obj.suspension_reason = "Client-initiated suspension"
            session_obj.suspended_at = datetime.now(timezone.utc)
            
            record_status_change(
                session=session,
                interview_session=session_obj,
                new_status=CandidateStatus.SUSPENDED,
                metadata={"reason": "client_initiated", "auto_suspended": False}
            )
            
            session.add(session_obj)
            session.commit()
            
            # Broadcast to admin dashboard
            from ..services.status_manager import _fire_async_broadcast
            _fire_async_broadcast(
                _broadcast_interview_suspended_event(interview_id, "client_initiated", session_obj.warning_count)
            )
            
            log_info(interview_id, "Interview suspended via explicit frontend event")
        else:
            log_debug(interview_id, "Interview_suspended received but session already suspended")
    except Exception as e:
        log_error(interview_id, f"Error processing Interview_suspended: {e}", exc_info=True)


# ========== VIDEO STREAMING HANDLERS ==========

async def handle_video_stream_connect(interview_id: int, websocket: WebSocket, current_user: User):
    """Handle video stream connection, security checks, and service startup."""
    try:
        if current_user is None:
            return False

        # Security: Candidate can only stream for THEIR OWN session.
        if current_user.role == UserRole.CANDIDATE:
             with Session(engine) as db_session:
                 session_obj = db_session.get(InterviewSession, interview_id)
                 if not session_obj or session_obj.candidate_id != current_user.id:
                     await websocket.close(code=4003, reason="Forbidden: Not your session")
                     log_warning(interview_id, f"Security: User {current_user.email} attempted to stream for unauthorized session")
                     return False

        await websocket.accept()
        
        from ..services.camera import CameraService
        camera_service = CameraService()
        
        if not camera_service.running:
            camera_service.start()

        # Register candidate face embedding for identity matching.
        # This is the enrolled photo embedding stored during candidate onboarding.
        if camera_service.face_detector and current_user.role == UserRole.CANDIDATE:
            try:
                with Session(engine) as db_s:
                    session_obj = db_s.get(InterviewSession, interview_id)
                    if session_obj:
                        candidate = db_s.get(User, session_obj.candidate_id)
                        if candidate and getattr(candidate, "face_embedding", None):
                            camera_service.face_detector.register_session_identity(
                                interview_id, candidate.face_embedding
                            )
                            log_info(interview_id, "Face identity registered for recognition.")
                        else:
                            log_warning(interview_id, "No enrolled face embedding found; recognition disabled for this session.")
            except Exception as e:
                log_error(interview_id, f"Failed to register face identity: {e}")
            
        log_info(interview_id, f"Video Stream connected (User: {current_user.email})")
        return True
    except Exception as e:
        log_error(interview_id, f"Error in handle_video_stream_connect: {e}")
        return False

async def process_video_frame(interview_id: int, websocket: WebSocket, data: bytes):
    """Process a single binary video frame and return AI results."""
    try:
        from ..services.camera import CameraService
        camera_service = CameraService()
        
        # Process via AI
        results = camera_service.process_external_frame(data, interview_id=interview_id)
        
        # Return results
        await websocket.send_json({
            "type": "proctoring_update",
            "interview_id": interview_id,
            "data": results,
            "timestamp": time.time()
        })
    except Exception as e:
        log_error(interview_id, f"Error processing video frame: {e}")

async def handle_video_stream_disconnect(interview_id: int):
    """Handle video stream disconnection."""
    log_info(interview_id, "Video Stream disconnected")
