from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, Depends
from sqlmodel import Session
from ..core.database import get_db as get_session
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
    session: Session = Depends(get_session)
):
    """
    WebSocket endpoint for candidates to receive real-time violation events.
    """
    try:
        # TODO: Implement token validation here
        await handler.handle_candidate_connect(interview_id, websocket, session)
        
        while True:
            try:
                data = await websocket.receive_json()
                await handler.process_candidate_message(interview_id, websocket, session, data)
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


# ========== ADMIN DASHBOARD STREAM ==========

@router.websocket("/api/dashboard/{interview_id}")
async def websocket_admin_dashboard(
    websocket: WebSocket,
    interview_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for admin dashboard to receive interview events.
    """
    try:
        # TODO: Implement token validation here
        await handler.handle_admin_connect(interview_id, websocket)
        
        while True:
            try:
                data = await websocket.receive_text()
                await handler.process_admin_message(interview_id, websocket, data)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                handler.log_error(interview_id, f"Error receiving admin message: {e}")
                break
            
    except WebSocketDisconnect:
        await handler.handle_admin_disconnect(interview_id, websocket)
    except Exception as e:
        handler.log_error(interview_id, f"Admin Dashboard WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
        await handler.handle_admin_disconnect(interview_id, websocket)
