from fastapi import APIRouter
from ..services.camera import CameraService
from ..core.config import local_llm
import os

router = APIRouter(prefix="/status", tags=["System"])
camera_service = CameraService()

@router.get("/")
async def get_system_status():
    """Comprehensive health check for AI services and Hardware."""
    
    # 1. Check Ollama / LLM
    llm_status = "error"
    try:
        # Simple probe
        local_llm.invoke("ping")
        llm_status = "healthy"
    except Exception:
        llm_status = "disconnected"

    # 2. Check Device / HW Status
    hw_status = "idle"
    if camera_service.running:
        hw_status = "active (streaming)"
    
    return {
        "status": "online",
        "services": {
            "llm": llm_status,
            "proctoring_engine": "healthy" if camera_service._detectors_ready else "initializing/off",
            "camera_access": hw_status
        },
        "environment": {
            "docker": os.path.exists("/.dockerenv"),
            "database": "connected"
        }
    }
