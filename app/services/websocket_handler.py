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
    _broadcast_interview_started_event
)

logger = get_logger(__name__)

# Standardized logging helper
def log_info(interview_id: int, message: str):
    logger.info(f"[Interview ID: {interview_id}] {message}")

def log_warning(interview_id: int, message: str):
    logger.warning(f"[Interview ID: {interview_id}] {message}")

def log_error(interview_id: int, message: str, exc_info=False):
    logger.error(f"[Interview ID: {interview_id}] {message}", exc_info=exc_info)

def log_debug(interview_id: int, message: str):
    logger.debug(f"[Interview ID: {interview_id}] {message}")

# ========== CANDIDATE HANDLERS ==========

async def handle_candidate_connect(interview_id: int, websocket: WebSocket, session: Session):
    """Handle initial candidate connection and status update."""
    try:
        await manager.connect_candidate(websocket, interview_id)
        log_info(interview_id, "Candidate WebSocket connected")
        
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()
        
        if session_obj and session_obj.status not in [InterviewStatus.COMPLETED, InterviewStatus.EXPIRED, InterviewStatus.CANCELLED]:
            old_status = session_obj.status
            # On reconnection, we always move back to CONNECTED status.
            # This requires the candidate to explicitly "Start/Resume" to go LIVE.
            session_obj.status = InterviewStatus.CONNECTED
            
            if old_status != session_obj.status:
                session.add(session_obj)
                session.commit()
                session.refresh(session_obj)
                log_info(interview_id, f"Status updated: {old_status} -> {session_obj.status}")
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
            
            if session_obj and session_obj.status not in [InterviewStatus.COMPLETED, InterviewStatus.EXPIRED, InterviewStatus.CANCELLED]:
                old_status = session_obj.status
                session_obj.status = InterviewStatus.DISCONNECTED
                
                if old_status != session_obj.status:
                    disconnect_session.add(session_obj)
                    disconnect_session.commit()
                    log_info(interview_id, "Status updated to DISCONNECTED")
    except Exception as e:
        log_error(interview_id, f"Error in handle_candidate_disconnect: {e}")

async def process_candidate_message(interview_id: int, websocket: WebSocket, session: Session, data: dict):
    """Dispatch candidate messages to specific handlers."""
    if not isinstance(data, dict):
        log_warning(interview_id, f"Received non-dict message: {data}")
        return

    msg_type = data.get("type")
    
    if msg_type == "login":
        await handle_login_event(interview_id, session, data)
    elif msg_type == "tab_switch":
        await handle_tab_switch_event(interview_id, session, data)
    elif msg_type == "tab_return":
        await handle_tab_return_event(interview_id, session, data)
    elif msg_type == "finish_interview":
        await handle_finish_interview_event(interview_id, websocket, session, data)
    elif msg_type == "start_interview":
        await handle_start_interview_event(interview_id, websocket, data)
    else:
        log_debug(interview_id, f"Unhandled message type: {msg_type}")

async def handle_login_event(interview_id: int, session: Session, data: dict):
    try:
        email = data.get("email")
        if not email:
            log_warning(interview_id, "Login event: No email field provided")
            return
            
        candidate = session.exec(
            select(User).where(User.email == email.lower())
        ).first()
        
        if candidate:
            candidate_info = {
                "candidate_id": candidate.id,
                "candidate_name": candidate.full_name,
                "candidate_email": candidate.email
            }
            await manager.broadcast_candidate_login(interview_id, candidate_info)
            log_info(interview_id, f"Candidate {email} login event broadcasted")
        else:
            log_warning(interview_id, f"Login event: Candidate with email {email} not found")
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
            
            add_violation(
                session=session,
                interview_session=session_obj,
                event_type="tab_switch",
                details=f"Tab switch detected (Attempt {session_obj.tab_switch_count})",
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

async def handle_tab_return_event(interview_id: int, session: Session, data: dict):
    try:
        session_obj = session.exec(
            select(InterviewSession).where(InterviewSession.id == interview_id)
        ).first()

        if session_obj and session_obj.tab_warning_active and session_obj.tab_switch_timestamp:
            now = datetime.now(timezone.utc)
            ts = session_obj.tab_switch_timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            
            elapsed = (now - ts).total_seconds()
            
            if elapsed > 30:
                session_obj.is_suspended = True
                session_obj.status = InterviewStatus.COMPLETED
                session_obj.is_completed = True
                session_obj.end_time = now
                session_obj.suspension_reason = "tab_switch_timeout"
                session_obj.suspended_at = now
                session_obj.tab_warning_active = False
                
                record_status_change(
                    session=session,
                    interview_session=session_obj,
                    new_status=CandidateStatus.SUSPENDED,
                    metadata={"reason": "tab_switch_timeout", "elapsed_seconds": elapsed}
                )
                
                from ..tasks.interview_tasks import process_session_results
                asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
                log_warning(interview_id, f"Suspended due to tab-switch timeout ({elapsed}s)")
            else:
                session_obj.tab_warning_active = False
                log_info(interview_id, f"Valid tab return after {elapsed}s")
            
            session.add(session_obj)
            session.commit()
    except Exception as e:
        log_error(interview_id, f"Error processing tab_return: {e}", exc_info=True)

async def handle_finish_interview_event(interview_id: int, websocket: WebSocket, session: Session, data: dict):
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

            await websocket.send_json({
                "type": "interview_finished_confirmation",
                "status": "success",
                "message": "Interview finished. Results are being processed."
            })
            log_info(interview_id, "Interview finished via WebSocket")
        else:
            log_warning(interview_id, "Finish interview: Session not found")
    except Exception as e:
        log_error(interview_id, f"Error processing finish_interview: {e}", exc_info=True)

async def handle_start_interview_event(interview_id: int, websocket: WebSocket, data: dict):
    try:
        # Update database status to LIVE
        with Session(engine) as db_session:
            session_obj = db_session.get(InterviewSession, interview_id)
            if session_obj and session_obj.status not in [InterviewStatus.COMPLETED, InterviewStatus.EXPIRED, InterviewStatus.CANCELLED]:
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
        
        await websocket.send_json({
            "type": "start_interview_confirmation",
            "status": "success"
        })
    except Exception as e:
        log_error(interview_id, f"Error processing start_interview: {e}", exc_info=True)


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


# ========== ADMIN HANDLERS ==========

async def handle_admin_connect(interview_id: int, websocket: WebSocket):
    """Handle initial admin dashboard connection."""
    try:
        await manager.connect_admin_dashboard(websocket, interview_id)
        log_info(interview_id, "Admin Dashboard WebSocket connected")
    except Exception as e:
        log_error(interview_id, f"Error in handle_admin_connect: {e}")

async def handle_admin_disconnect(interview_id: int, websocket: WebSocket):
    """Handle admin dashboard disconnection."""
    try:
        manager.disconnect_admin_dashboard(websocket, interview_id)
        log_info(interview_id, "Admin Dashboard WebSocket disconnected")
    except Exception as e:
        log_error(interview_id, f"Error in handle_admin_disconnect: {e}")

async def process_admin_message(interview_id: int, websocket: WebSocket, data: str):
    """Handle messages received from the admin dashboard."""
    try:
        log_debug(interview_id, f"Received from admin dashboard: {data}")
        # Add future admin-to-backend message handling here
    except Exception as e:
        log_error(interview_id, f"Error processing admin message: {e}")
