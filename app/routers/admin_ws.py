from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from ..auth.dependencies import get_admin_user_ws
from ..models.db_models import User
from fastapi import Depends
from ..services.websocket_manager import manager
from ..core.logger import get_logger
import json

logger = get_logger(__name__)
router = APIRouter(tags=["Admin Realtime"])

# TEMPORARY TEST ENDPOINT - No authentication, minimal logic
@router.websocket("/test-ws")
async def test_ws_minimal(websocket: WebSocket):
    """Minimal WS endpoint for testing if websockets work at all."""
    logger.info("🧪 TEST-WS: Connection attempt")
    await websocket.accept()
    logger.info("🧪 TEST-WS: Connection accepted")
    await websocket.send_text(json.dumps({"status": "connected", "message": "Test WS working!"}))
    logger.info("🧪 TEST-WS: Sent test message")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("🧪 TEST-WS: Disconnected")

@router.websocket("/dashboard/ws")
async def admin_dashboard_ws(
    websocket: WebSocket, 
    token: Optional[str] = Query(None),
):
    """
    Real-time Admin Dashboard Stream.
    Requires Admin Authentication (Token passed as query param or cookie).
    """
    from fastapi import status
    from jose import jwt, JWTError
    from ..auth.security import SECRET_KEY, ALGORITHM
    from sqlmodel import Session, select
    from ..core.database import get_db as get_session_func
    from ..models.db_models import User, UserRole
    
    print(f"DEBUG: admin_dashboard_ws handshake for {token[:10] if token else 'None'}", flush=True)
    logger.info(f"🔍 Admin WS handshake initiated. Token from query: {bool(token)}")
    
    # Manual token extraction (mimic get_current_user_ws)
    if not token:
        token = websocket.cookies.get("access_token")
        logger.info(f"🔍 Token from cookie: {bool(token)}")
    
    if not token:
        logger.warning("❌ Token missing from query and cookie")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token missing")
        return
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        logger.info(f"✅ Token decoded for email: {email}")
        if not email:
            logger.warning("❌ Invalid token - no email (sub) in payload")
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except JWTError as e:
        logger.error(f"❌ JWT decode error: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Get user from DB
    from ..core.database import engine
    with Session(engine) as db_session:
        user = db_session.exec(select(User).where(User.email == email)).first()
    
    if not user:
        logger.warning(f"❌ User not found: {email}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return
    
    logger.info(f"✅ User found: {email} with role: {user.role}")
    
    # Check admin role
    if user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        logger.warning(f"❌ Non-admin user attempted WS: {email} with role {user.role}")
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Admin role required")
        return
    
    logger.info(f"✅ Admin WS auth passed for: {email}")
    
    # All checks passed - accept the connection
    await websocket.accept()
    logger.info(f"✅ WebSocket accepted for admin: {email}")
    
    await manager.connect_admin(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        logger.info(f"👋 Admin WS disconnected: {email}")
        manager.disconnect_admin(websocket)
    except Exception as e:
        logger.error(f"❌ Admin WS Error: {e}")
        manager.disconnect_admin(websocket)
