from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..auth.dependencies import get_admin_user_ws
from ..models.db_models import User
from fastapi import Depends
from ..services.websocket_manager import manager
from ..core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Admin Realtime"])

@router.websocket("/dashboard/ws")
async def admin_dashboard_ws(
    websocket: WebSocket, 
    current_user: User = Depends(get_admin_user_ws)
):
    """
    Real-time Admin Dashboard Stream.
    Requires Admin Authentication (Token passed as query param).
    """
    if not current_user:
        return
    
    await manager.connect_admin(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect_admin(websocket)
    except Exception as e:
        logger.error(f"Admin WS Error: {e}")
        manager.disconnect_admin(websocket)
