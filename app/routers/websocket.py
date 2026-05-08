import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, Depends
from sqlmodel import Session, select
from datetime import datetime, timezone
from ..core.database import get_db as get_session
from ..models.db_models import User, InterviewSession, CandidateStatus
from ..core.logger import get_logger
from ..services.websocket_manager import manager
from ..services.status_manager import add_violation, record_status_change

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

# ========== CANDIDATE VIOLATION STREAM ==========

@router.websocket("/api/interview/{interview_id}")
async def websocket_candidate_violations(
    websocket: WebSocket,
    interview_id: int,
    token: str = Query(...),
    session: Session = Depends(get_session)
):
    print(f"DEBUG: websocket_candidate_violations handshake for {interview_id}", flush=True)
    """
    WebSocket endpoint for candidates to receive real-time violation events.
    
    Sends:
    - ViolationEvent: When a violation is detected (tab switch, wrong face, etc.)
    - AdminDashboardEvent (interview_suspended): When violation threshold is exceeded
    
    The token parameter should be the candidate's access token for authentication.
    """
    try:
        # TODO: Implement token validation here
        # For now, we'll connect directly - in production add:
        # validate_access_token(token)
        
        await manager.connect_candidate(websocket, interview_id)
        logger.info(f"Candidate WebSocket connected: Interview {interview_id}")
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"Received from candidate {interview_id}: {data}")
                
                # Handle specialized login message
                if isinstance(data, dict) and data.get("type") == "login":
                    try:
                        email = data.get("email")
                        logger.info(f"DEBUG: Processing login message for {email} in interview {interview_id}")
                        if email:
                            # Fetch candidate details
                            candidate = session.exec(
                                select(User).where(User.email == email.lower())
                            ).first()
                            
                            if candidate:
                                logger.info(f"DEBUG: Found candidate {candidate.full_name} for email {email}")
                                # Prepare candidate info for broadcast
                                candidate_info = {
                                    "candidate_id": candidate.id,
                                    "candidate_name": candidate.full_name,
                                    "candidate_email": candidate.email
                                }
                                # Broadcast login event to admin
                                await manager.broadcast_candidate_login(interview_id, candidate_info)
                                logger.info(f"Candidate {email} login event broadcasted for interview {interview_id}")
                            else:
                                logger.warning(f"Login event: Candidate with email {email} not found in database")
                        else:
                            logger.warning(f"Login event: No email field provided in login message for interview {interview_id}")
                    except Exception as e:
                        logger.error(f"Error processing login message for interview {interview_id}: {e}", exc_info=True)

                # Handle tab switch event
                elif isinstance(data, dict) and data.get("type") == "tab_switch":
                    try:
                        # Optional: Validate interview_id from payload matches URL
                        payload_id = data.get("interview_id")
                        if payload_id and int(payload_id) != interview_id:
                            logger.warning(f"Tab switch payload ID mismatch: URL={interview_id}, Payload={payload_id}")

                        # Fetch interview session
                        session_obj = session.exec(
                            select(InterviewSession).where(InterviewSession.id == interview_id)
                        ).first()

                        if session_obj and not session_obj.is_completed and not session_obj.is_suspended:
                            now = datetime.now(timezone.utc)
                            session_obj.tab_switch_count += 1
                            session_obj.tab_switch_timestamp = now
                            session_obj.tab_warning_active = True
                            
                            # Log violation and notify admin
                            add_violation(
                                session=session,
                                interview_session=session_obj,
                                event_type="tab_switch",
                                details=f"Tab switch detected (Attempt {session_obj.tab_switch_count})",
                                force_severity="warning"
                            )
                            
                            # Check for suspension (handled inside add_violation now, but we trigger task here)
                            if session_obj.is_suspended:
                                import asyncio
                                from ..tasks.interview_tasks import process_session_results
                                asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
                                logger.info(f"Interview {interview_id} suspended via tab-switch threshold, triggering evaluation.")

                            session.add(session_obj)
                            session.commit()
                            logger.info(f"Tab switch handled for interview {interview_id} (Count: {session_obj.tab_switch_count})")
                    except Exception as e:
                        logger.error(f"Error processing tab_switch for interview {interview_id}: {e}", exc_info=True)

                # Handle tab return event
                elif isinstance(data, dict) and data.get("type") == "tab_return":
                    try:
                        # Optional: Validate interview_id from payload matches URL
                        payload_id = data.get("interview_id")
                        if payload_id and int(payload_id) != interview_id:
                            logger.warning(f"Tab return payload ID mismatch: URL={interview_id}, Payload={payload_id}")

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
                                # Terminate due to timeout
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
                                
                                import asyncio
                                from ..tasks.interview_tasks import process_session_results
                                asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
                                
                                logger.warning(f"Interview {interview_id} suspended due to tab-switch timeout ({elapsed}s), triggering evaluation.")
                            else:
                                # Valid return within 30s
                                session_obj.tab_warning_active = False
                                logger.info(f"Valid tab return for interview {interview_id} after {elapsed}s")
                            
                            session.add(session_obj)
                            session.commit()
                    except Exception as e:
                        logger.error(f"Error processing tab_return for interview {interview_id}: {e}", exc_info=True)

                # Handle finish interview event
                elif isinstance(data, dict) and data.get("type") == "finish_interview":
                    try:
                        # Optional: Validate interview_id from payload
                        payload_id = data.get("interview_id")
                        if payload_id and int(payload_id) != interview_id:
                            logger.warning(f"Finish interview payload ID mismatch: URL={interview_id}, Payload={payload_id}")

                        # Fetch interview session
                        session_obj = session.exec(
                            select(InterviewSession).where(InterviewSession.id == interview_id)
                        ).first()

                        if session_obj:
                            import asyncio
                            from ..services.status_manager import complete_interview_session
                            from ..tasks.interview_tasks import process_session_results
                            from ..services.camera import CameraService

                            # 1. Complete the session (handles status and broadcasting)
                            complete_interview_session(
                                session=session,
                                interview_session=session_obj,
                                reason="manual_finish",
                                current_status_label="Completed",
                            )
                            
                            # 2. Process results in background thread (AI tasks)
                            asyncio.create_task(asyncio.to_thread(process_session_results, interview_id))
                            
                            # 3. Cleanup proctoring resources
                            try:
                                CameraService().clear_session(interview_id)
                            except Exception as cam_err:
                                logger.error(f"Failed to clear camera session {interview_id}: {cam_err}")

                            # 4. Confirm to candidate
                            await websocket.send_json({
                                "type": "interview_finished_confirmation",
                                "status": "success",
                                "message": "Interview finished. Results are being processed."
                            })
                            logger.info(f"Interview {interview_id} finished via WebSocket")
                        else:
                            logger.warning(f"Finish interview: Session {interview_id} not found")
                    except Exception as e:
                        logger.error(f"Error processing finish_interview for interview {interview_id}: {e}", exc_info=True)

                # Handle start interview event (Manual trigger from frontend)
                elif isinstance(data, dict) and data.get("type") == "start_interview":
                    try:
                        from ..services.status_manager import _broadcast_interview_started_event
                        # Trigger the broadcast that used to be in the REST API
                        await _broadcast_interview_started_event(interview_id)
                        logger.info(f"Interview {interview_id} start event triggered via WebSocket")
                        
                        # Return confirmation to candidate
                        await websocket.send_json({
                            "type": "start_interview_confirmation",
                            "status": "success"
                        })
                    except Exception as e:
                        logger.error(f"Error processing start_interview for interview {interview_id}: {e}", exc_info=True)
                
            except WebSocketDisconnect:
                # Re-raise to catch it in the outer block
                raise
            except json.JSONDecodeError:
                # Handle non-JSON messages (like raw strings)
                try:
                    raw_data = await websocket.receive_text()
                    logger.debug(f"Received non-JSON from candidate {interview_id}: {raw_data}")
                except Exception:
                    pass
            except Exception as e:
                # Other message processing errors
                logger.error(f"Error receiving message from candidate {interview_id}: {e}")
                break
            
    except WebSocketDisconnect:
        await manager.disconnect_candidate(websocket, interview_id)
        logger.info(f"Candidate WebSocket disconnected (Cleanly): Interview {interview_id}")
    except Exception as e:
        logger.error(f"Candidate WebSocket error {interview_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
        await manager.disconnect_candidate(websocket, interview_id)


# ========== ADMIN DASHBOARD STREAM ==========

@router.websocket("/api/dashboard/{interview_id}")
async def websocket_admin_dashboard(
    websocket: WebSocket,
    interview_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for admin dashboard to receive interview events.
    
    Sends:
    - ViolationEvent: Real-time violation updates (tab switch, face detection, etc.)
    - AdminDashboardEvent: Major status changes
        - interview_started: Interview transitioned to LIVE
        - interview_suspended: Violation threshold exceeded
        - interview_completed: Interview finished
        - interview_expired: Interview time expired
    
    The token parameter should be the admin's access token for authentication.
    """
    try:
        # TODO: Implement token validation here
        # For now, we'll connect directly - in production add:
        # validate_admin_token(token)
        
        await manager.connect_admin_dashboard(websocket, interview_id)
        logger.info(f"Admin Dashboard WebSocket connected: Interview {interview_id}")
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Client can send heartbeat or ping to keep connection alive
            logger.debug(f"Received from admin dashboard {interview_id}: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect_admin_dashboard(websocket, interview_id)
        logger.info(f"Admin Dashboard WebSocket disconnected: Interview {interview_id}")
    except Exception as e:
        logger.error(f"Admin Dashboard WebSocket error {interview_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
        manager.disconnect_admin_dashboard(websocket, interview_id)
