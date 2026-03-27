from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from ..services.camera import CameraService
from ..core.config import local_llm, IS_ORCHESTRATOR

from ..schemas.shared.api_response import ApiResponse
from ..core.database import engine
from sqlmodel import text
import os
import asyncio
from ..core.logger import get_logger
import logging

logger = get_logger(__name__)

router = APIRouter(prefix="/status", tags=["System"])
camera_service = CameraService()

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

@router.get("/", response_model=ApiResponse[dict])
async def get_system_status(interview_id: Optional[int] = Query(None)):
    """Comprehensive health check for AI services (Isolate by session)."""
    from ..services.interview import USE_MODAL, get_modal_evaluator

    llm_status = "error"
    modal_status = "disabled"

    if USE_MODAL:
        try:
            evaluator_cls = get_modal_evaluator()
            if evaluator_cls:
                # Check if we can obtain the remote method reference
                # (This verifies the class exists in the remote registry)
                if hasattr(evaluator_cls, "evaluate"):
                    modal_status = "healthy (connected)"
                else:
                    modal_status = "error (method 'evaluate' not found on remote class)"
            else:
                from ..services.interview import _modal_lookup_error
                modal_status = f"error ({_modal_lookup_error or 'evaluator ref not obtained'})"
        except Exception as e:
            logger.error(f"Modal evaluator lookup failed: {e}", exc_info=True)
            modal_status = "error (internal connection failure)"
        llm_status = modal_status # Modal is the primary LLM
    else:
        # Check Groq First (Primary Fallback)
        if os.getenv("GROQ_API_KEY"):
            llm_status = "healthy (Groq API fallback)"
        else:
            if not IS_ORCHESTRATOR:
                try:
                    local_llm.invoke("ping")
                    llm_status = "healthy (local Ollama)"
                except Exception:
                    # Fallback to Hugging Face Inference API check
                    if os.getenv("HF_TOKEN"):
                        llm_status = "healthy (HF Inference API fallback)"
                    else:
                        llm_status = "disconnected (local Ollama not found & no fallback keys)"
            else:
                # Orchestrator mode with no remote keys
                if os.getenv("HF_TOKEN"):
                    llm_status = "healthy (HF Inference API fallback)"
                else:
                    llm_status = "disabled (Orchestrator Mode - Local Ollama skipped)"

    
    # Check Database Status
    db_status = "unknown"
    db_detail = ""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
        db_detail = str(e)
        logger.error(f"Database health check failed: {e}")

    hw_status = "idle"
    if camera_service.running:
        hw_status = "active (streaming)"
    
    # Enhanced proctoring status
    proctoring_status = "initializing/off"
    proctoring_details = {}
    if camera_service._detectors_ready:
        proctoring_status = "healthy"
        proctoring_details = {
            "face_detector": "✓ active" if camera_service.face_detector else "✗ failed",
            "gaze_detector": "✓ active" if camera_service.gaze_detector else "✗ failed"
        }
    else:
        proctoring_details = {
            "status": "Initializing detectors...",
            "face_detector": "initializing",
            "gaze_detector": "initializing"
        }
    
    # Get current warning (handle None interview_id)
    current_warning = camera_service.get_current_warning(interview_id) if interview_id else None
    
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
        camera_service.add_listener(camera_status_callback)
        _listener_registered = True
        
    try:
        await websocket.send_json({"warning": camera_service.get_current_warning(interview_id)})
        while True:
            await websocket.receive_text() # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, interview_id)
