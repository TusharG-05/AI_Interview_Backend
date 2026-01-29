from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.camera import CameraService
from ..core.config import local_llm
import os
import asyncio

router = APIRouter(prefix="/status", tags=["System"])
camera_service = CameraService()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_json({"warning": message})
            except Exception:
                pass

manager = ConnectionManager()
_listener_registered = False

def camera_status_callback(warning_key):
    """Bridge for CameraService alerts to WebSockets."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(warning_key), loop)
    except Exception:
        pass

@router.get("/")
async def get_system_status():
    """Comprehensive health check for AI services and Hardware."""
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
            "current_warning": camera_service.get_current_warning()
        },
        "environment": {
            "docker": os.path.exists("/.dockerenv"),
            "database": "connected"
        }
    }

@router.websocket("/ws")
async def websocket_status(websocket: WebSocket):
    """Real-time proctoring alert feed for frontend integration."""
    global _listener_registered
    await manager.connect(websocket)
    
    if not _listener_registered:
        camera_service.add_listener(camera_status_callback)
        _listener_registered = True
        
    try:
        await websocket.send_json({"warning": camera_service.get_current_warning()})
        while True:
            await websocket.receive_text() # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
