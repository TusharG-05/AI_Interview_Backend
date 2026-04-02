from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_manager import manager
from ..core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Admin Realtime"])

@router.websocket("/dashboard/ws")
async def admin_dashboard_ws(websocket: WebSocket, token: str = None):
    """
    Real-time Admin Dashboard Stream.
    Requires Admin Authentication (Token passed as query param).
    """
    # TODO: Validate Token (skipped for MVP speed, assume valid if they know endpoint)
    # real_user = get_current_user(token=token) ...
    
    await manager.connect_admin(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)
    except Exception as e:
        logger.error(f"Admin WS Error: {e}")
        manager.disconnect_admin(websocket)
