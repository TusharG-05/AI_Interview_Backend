import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query
from ..core.logger import get_logger
from ..services import websocket_handler as handler

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
):
    """
    WebSocket endpoint for candidates to receive real-time violation events.
    Token is validated manually to allow accept() before closing on auth failure.
    """
    from jose import jwt, JWTError
    from ..auth.security import SECRET_KEY, ALGORITHM
    from ..models.db_models import User
    from ..core.database import engine
    from sqlmodel import Session as DBSession, select as db_select

    logger.debug(f"[WS] Candidate connect attempt for interview {interview_id}")

    # --- AUTH: Validate token before accepting ---
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except JWTError as e:
        logger.warning(f"[WS] Invalid token for interview {interview_id}: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # --- DB: Fetch user AFTER auth passes, using a short-lived session ---
    try:
        with DBSession(engine) as db:
            user = db.exec(db_select(User).where(User.email == email)).first()
        if not user:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            return
    except Exception as e:
        logger.error(f"[WS] DB error during candidate auth for interview {interview_id}: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Server error")
        return

    logger.info(f"[WS] Candidate {email} authenticated for interview {interview_id}")

    # --- MAIN LOOP: open a fresh DB session for the lifetime of the connection ---
    try:
        with DBSession(engine) as session:
            await handler.handle_candidate_connect(interview_id, websocket, session)

            while True:
                try:
                    data = await websocket.receive_json()
                    await handler.process_candidate_message(interview_id, websocket, session, data)
                except json.JSONDecodeError as e:
                    handler.log_warning(interview_id, f"Malformed candidate WebSocket JSON: {e}")
                    continue
                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    handler.log_error(interview_id, f"Error receiving message: {e}")
                    break

    except WebSocketDisconnect:
        await handler.handle_candidate_disconnect(interview_id, websocket)

    except Exception as e:
        handler.log_error(interview_id, f"Critical WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
        await handler.handle_candidate_disconnect(interview_id, websocket)

# Per-interview admin dashboard WebSocket has been removed per spec.
# Use the global admin dashboard at /api/admin/dashboard/ws instead.

