from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Optional
from ..models.db_models import UserRole
from ..services.websocket_manager import manager
from ..core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Admin Realtime"])


@router.websocket("/dashboard/ws")
async def admin_dashboard_ws(
    websocket: WebSocket, 
    token: Optional[str] = Query(None),
):
    """
    Global Admin Dashboard WebSocket.
    
    Receives real-time updates for all active interviews created by the connected admin.
    SUPER_ADMIN receives all broadcasts. ADMIN only receives events for their own interviews.
    
    Endpoint: wss://<api-domain>/api/admin/dashboard/ws?token=<admin_jwt>
    """
    from jose import jwt, JWTError
    from ..auth.security import SECRET_KEY, ALGORITHM
    from sqlmodel import Session, select
    from ..core.database import engine
    from ..models.db_models import User
    
    # Manual token extraction
    if not token:
        token = websocket.cookies.get("access_token")
    
    if not token:
        logger.warning("Admin WS: Token missing from query and cookie")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token missing")
        return
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except JWTError as e:
        logger.warning(f"Admin WS: JWT decode error: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Get user from DB
    with Session(engine) as db_session:
        user = db_session.exec(select(User).where(User.email == email)).first()
    
    if not user:
        logger.warning(f"Admin WS: User not found: {email}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return
    
    # Check admin role
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        logger.warning(f"Admin WS: Non-admin user attempted connection: {email} ({user.role})")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Admin role required")
        return
    
    logger.info(f"Admin WS: Auth passed for {email} ({user.role})")
    
    # All checks passed - accept the connection
    await websocket.accept()
    await manager.connect_admin(websocket, user.id, user.role)
    
    # Send initial dashboard metrics right away
    try:
        from ..services.status_manager import compute_dashboard_metrics
        dashboard_metrics = compute_dashboard_metrics()
        await websocket.send_json({
            "event_type": "Initial_dashboard_data",
            "data": {
                "dashboard_data": dashboard_metrics
            }
        })
    except Exception as e:
        logger.error(f"Admin WS: Failed to send initial metrics: {e}")
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        logger.info(f"Admin WS: Disconnected: {email}")
        manager.disconnect_admin(websocket)
    except Exception as e:
        logger.error(f"Admin WS: Error: {e}")
        manager.disconnect_admin(websocket)
