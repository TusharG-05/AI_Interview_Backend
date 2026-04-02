from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from ..services.camera import CameraService
from ..services.interview import get_modal_evaluator
from ..core.config import local_llm, IS_ORCHESTRATOR, USE_MODAL

from ..schemas.shared.api_response import ApiResponse
from ..core.database import engine
from sqlmodel import text
import os
import asyncio
from ..core.logger import get_logger
import logging

logger = get_logger(__name__)

router = APIRouter(prefix="/status", tags=["System"])
_camera_service = None

def get_camera_service():
    global _camera_service
    if _camera_service is None:
        from ..services.camera import CameraService
        _camera_service = CameraService()
    return _camera_service

class ConnectionManager:
    def __init__(self):
        # {interview_id: [WebSocket]}
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, interview_id: int):
        await websocket.accept()
        if interview_id not in self.active_connections:
            self.active_connections[interview_id] = []
        self.active_connections[interview_id].append(websocket)

    def disconnect(self, websocket: WebSocket, interview_id: int):
        if interview_id in self.active_connections:
            if websocket in self.active_connections[interview_id]:
                self.active_connections[interview_id].remove(websocket)

    async def broadcast(self, interview_id: int, message: str):
        if interview_id in self.active_connections:
            for connection in self.active_connections[interview_id]:
                try:
                    await connection.send_json({"warning": message})
                except Exception as e:
                    print(f"WebSocket Broadcast Error: {e}")

manager = ConnectionManager()
_listener_registered = False

def camera_status_callback(interview_id: int, warning_key: str):
    """Bridge for CameraService alerts to WebSockets (Filtered by Session)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(manager.broadcast(interview_id, warning_key), loop)
    except Exception as e:
        print(f"Callback Bridge Error: {e}")

def _get_llm_status() -> str:
    from ..services.interview import get_modal_evaluator
    from ..core.config import USE_MODAL
    if USE_MODAL:
        try:
            evaluator_cls = get_modal_evaluator()
            if evaluator_cls:
                return "healthy (connected)" if hasattr(evaluator_cls, "evaluate") else "error (method 'evaluate' not found on remote class)"
            from ..services.interview import _modal_lookup_error
            return f"error ({_modal_lookup_error or 'evaluator ref not obtained'})"
        except Exception as e:
            logger.error(f"Modal evaluator lookup failed: {e}", exc_info=True)
            return "error (internal connection failure)"
            
    if os.getenv("GROQ_API_KEY"):
        return "healthy (Groq API fallback)"
        
    if not IS_ORCHESTRATOR:
        try:
            from ..core.config import local_llm
            local_llm.invoke("ping")
            return "healthy (local Ollama)"
        except Exception:
            return "healthy (HF Inference API fallback)" if os.getenv("HF_TOKEN") else "disconnected (local Ollama not found & no fallback keys)"
            
    return "healthy (HF Inference API fallback)" if os.getenv("HF_TOKEN") else "disabled (Orchestrator Mode - Local Ollama skipped)"

def _get_db_status() -> tuple[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return "healthy", ""
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "unhealthy", str(e)

def _get_proctoring_status() -> tuple[str, dict]:
    service = get_camera_service()
    if service._detectors_ready:
        return "healthy", {
            "face_detector": "✓ active" if service.face_detector else "✗ failed",
            "gaze_detector": "✓ active" if service.gaze_detector else "✗ failed"
        }
    return "unknown", {
        "status": "initializing / disabled",
        "reason": "Wait for cameras to start or running in Orchestrator Mode"
    }

@router.get("/", response_model=ApiResponse[dict])
async def get_system_status(interview_id: Optional[int] = Query(None)):
    """Comprehensive health check for AI services (Isolate by session)."""
    llm_status = _get_llm_status()
    db_status, db_detail = _get_db_status()
    hw_status = "active (streaming)" if get_camera_service().running else "idle"
    proctoring_status, proctoring_details = _get_proctoring_status()
    modal_status = _get_llm_status() if USE_MODAL else "disabled"
    
    # Get current warning (handle None interview_id)
    current_warning = get_camera_service().get_current_warning(interview_id) if interview_id else None
    
    return ApiResponse(
        status_code=200,
        data={
            "status": "online",
            "services": {
                "llm": llm_status,
                "database": {
                    "status": db_status,
                    "detail": db_detail if db_status == "unhealthy" else "Connected"
                },
                "modal_enabled": USE_MODAL,
                "modal_status": modal_status,
                "proctoring_engine": proctoring_status,
                "proctoring_details": proctoring_details,
                "camera_access": hw_status,
                "current_warning": current_warning
            }
        },
        message="System status retrieved successfully"
    )

@router.websocket("/ws")
async def websocket_status(websocket: WebSocket, interview_id: int = None):
    """Real-time proctoring alert feed (Isolate by Session)."""
    global _listener_registered
    
    if interview_id is None:
        await websocket.close(code=4000, reason="interview_id parameter is required")
        return
        
    await manager.connect(websocket, interview_id)
    
    if not _listener_registered:
        get_camera_service().add_listener(camera_status_callback)
        _listener_registered = True
        
    try:
        await websocket.send_json({"warning": get_camera_service().get_current_warning(interview_id)})
        while True:
            await websocket.receive_text() # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, interview_id)
