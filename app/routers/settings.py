from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.camera import CameraService
from ..core.config import local_llm
from ..schemas.api_response import ApiResponse
import os
import asyncio

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
async def get_system_status(interview_id: int):
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
            modal_status = f"error ({str(e)})"
        llm_status = modal_status # Modal is the primary LLM
    else:
        try:
            local_llm.invoke("ping")
            llm_status = "healthy"
        except Exception:
            llm_status = "disconnected (local Ollama not found)"

    hw_status = "idle"
    if camera_service.running:
        hw_status = "active (streaming)"
    
    return ApiResponse(
        status_code=200,
        data={
            "status": "online",
            "services": {
                "llm": llm_status,
                "modal_enabled": USE_MODAL,
                "modal_status": modal_status,
                "proctoring_engine": "healthy" if camera_service._detectors_ready else "initializing/off",
                "camera_access": hw_status,
                "current_warning": camera_service.get_current_warning(interview_id)
            }
        },
        message="System status retrieved successfully"
    )

@router.websocket("/ws")
async def websocket_status(websocket: WebSocket, interview_id: int):
    """Real-time proctoring alert feed (Isolate by Session)."""
    global _listener_registered
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
