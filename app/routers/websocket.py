from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query
from ..core.logger import get_logger
from ..services.websocket_manager import manager

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
    token: str = Query(...)
):
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
            data = await websocket.receive_text()
            # Client can send heartbeat or ping to keep connection alive
            logger.debug(f"Received from candidate {interview_id}: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect_candidate(websocket, interview_id)
        logger.info(f"Candidate WebSocket disconnected: Interview {interview_id}")
    except Exception as e:
        logger.error(f"Candidate WebSocket error {interview_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
        manager.disconnect_candidate(websocket, interview_id)


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
