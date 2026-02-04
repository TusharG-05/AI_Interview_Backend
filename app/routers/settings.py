from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.camera import CameraService
from ..core.config import local_llm
import os
import asyncio

router = APIRouter(prefix="/status", tags=["System"])
camera_service = CameraService()

class ConnectionManager:
    def __init__(self):
        # {session_id: [WebSocket]}
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)

    async def broadcast(self, session_id: int, message: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json({"warning": message})
                except Exception:
                    pass

manager = ConnectionManager()
_listener_registered = False

def camera_status_callback(session_id: int, warning_key: str):
    """Bridge for CameraService alerts to WebSockets (Filtered by Session)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(session_id, warning_key), loop)
    except Exception:
        pass

@router.get("/")
async def get_system_status(session_id: int):
    """Comprehensive health check for AI services (Isolate by session)."""
    llm_status = "error"
    try:
        local_llm.invoke("ping")
        llm_status = "healthy"
    except Exception:
        llm_status = "disconnected"

    hw_status = "idle"
    if camera_service.running:
        hw_status = "active (streaming)"
    
    return {
        "status": "online",
        "services": {
            "llm": llm_status,
            "proctoring_engine": "healthy" if camera_service._detectors_ready else "initializing/off",
            "camera_access": hw_status,
            "current_warning": camera_service.get_current_warning(session_id)
        }
    }

@router.websocket("/ws")
async def websocket_status(websocket: WebSocket, session_id: int):
    """Real-time proctoring alert feed (Isolate by Session)."""
    global _listener_registered
    await manager.connect(websocket, session_id)
    
    if not _listener_registered:
        camera_service.add_listener(camera_status_callback)
        _listener_registered = True
        
    try:
        await websocket.send_json({"warning": camera_service.get_current_warning(session_id)})
        while True:
            await websocket.receive_text() # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
