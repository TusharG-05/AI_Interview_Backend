"""
Candidate Interview WebSocket Router

Endpoint: wss://<api-domain>/ws/api/interview/{interview_id}?token=<candidate_jwt>
Role:     CANDIDATE only (must be assigned to this interview_id)

The candidate sends JSON messages to report lifecycle events and proctoring violations.
The backend does NOT push any messages back to the candidate over this connection.
"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlmodel import Session as DBSession, select as db_select

from ..core.logger import get_logger
from ..services import websocket_handler as handler
from ..services.websocket_manager import manager

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["Candidate Realtime"])


@router.websocket("/api/interview/{interview_id}")
async def candidate_interview_ws(
    websocket: WebSocket,
    interview_id: int,
    token: str = Query(...),
):
    """
    Candidate Interview WebSocket.

    The candidate sends these event types (Frontend → Backend):
      - Interview_login        → marks session CONNECTED, broadcasts to admins
      - Interview_started      → marks session LIVE, broadcasts to admins
      - Interview_disconnected → marks session DISCONNECTED, broadcasts to admins
      - Interview_finished     → completes session, triggers evaluation, broadcasts
      - Interview_suspended    → suspends session (client confirmation)
      - Proctoring_violation   → logs violation (violation_type: tab_switch | no_face | ...)

    The backend does NOT send any messages back to the candidate.
    """
    from jose import jwt, JWTError
    from ..auth.security import SECRET_KEY, ALGORITHM
    from ..models.db_models import User, UserRole, InterviewSession
    from ..core.database import engine

    # ── 1. Token validation ────────────────────────────────────────────────
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise JWTError("Missing 'sub' claim")
    except JWTError as e:
        logger.warning(f"[WS] Candidate auth failed for interview {interview_id}: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # ── 2. User lookup ────────────────────────────────────────────────────
    try:
        with DBSession(engine) as db:
            user = db.exec(db_select(User).where(User.email == email)).first()
    except Exception as e:
        logger.error(f"[WS] DB error for interview {interview_id}: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Server error")
        return

    if not user:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return

    # ── 3. Role check: must be CANDIDATE ─────────────────────────────────
    if user.role != UserRole.CANDIDATE:
        logger.warning(f"[WS] Non-candidate role ({user.role}) attempted candidate WS")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Candidate role required")
        return

    # ── 4. Ownership check: candidate must belong to this interview ───────
    try:
        with DBSession(engine) as db:
            session_obj = db.get(InterviewSession, interview_id)
    except Exception as e:
        logger.error(f"[WS] DB error checking interview ownership: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Server error")
        return

    if not session_obj or session_obj.candidate_id != user.id:
        logger.warning(f"[WS] Candidate {email} is not assigned to interview {interview_id}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not your interview")
        return

    # ── 5. Accept & register ──────────────────────────────────────────────
    if manager.has_candidate(interview_id):
        logger.warning(f"[WS] Interview {interview_id} already has an active connection. Rejecting new connection for {email}.")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Interview is already active on another device.")
        return

    await websocket.accept()
    manager.register_candidate(websocket, interview_id)
    logger.info(f"[WS] Candidate {email} connected to interview {interview_id}")

    # ── 6. Main loop ──────────────────────────────────────────────────────
    try:
        with DBSession(engine) as session:
            await handler.handle_candidate_connect(interview_id, session)

            while True:
                try:
                    data = await websocket.receive_json()
                    await handler.process_candidate_message(interview_id, websocket, session, data)
                except json.JSONDecodeError as e:
                    handler.log_warning(interview_id, f"Malformed JSON ignored: {e}")
                    continue
                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    handler.log_error(interview_id, f"Message handling error: {e}")
                    break

    except WebSocketDisconnect:
        await handler.handle_candidate_disconnect(interview_id)

    except Exception as e:
        handler.log_error(interview_id, f"Critical WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except Exception:
            pass
        await handler.handle_candidate_disconnect(interview_id)
