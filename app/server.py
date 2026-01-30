import contextlib
import os
from fastapi import FastAPI
from .routers import video, settings, admin, interview, auth, candidate
from .core.database import init_db
from .core.logger import setup_logging, get_logger

logger = get_logger(__name__)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting Application (API-Only Mode)...")
    
    # MONKEY PATCH: Fix speechbrain vs torchaudio 2.x incompatibility
    import torchaudio
    if not hasattr(torchaudio, "list_audio_backends"):
        logger.warning("Monkey Patching torchaudio.list_audio_backends for SpeechBrain")
        torchaudio.list_audio_backends = lambda: ["soundfile"]

    # Initialize database
    init_db()
    
    from .services.camera import CameraService
    from .routers.interview import audio_service
    
    # Pre-warm models in background
    import threading
    def warm_up():
        logger.info("Warm-up: Loading AI Models (Whisper, LLM)...")
        from .core.config import local_llm
        try:
            _ = audio_service.stt_model
            local_llm.invoke("Hello")
            logger.info("Warm-up: AI Models Ready.")
        except Exception as e:
            logger.error(f"Warm-up failed: {e}")
    
    # threading.Thread(target=warm_up, daemon=True).start()
    logger.info("Warm-up: Validation skipped for stability.")
    
    service = CameraService()
    yield
    
    logger.info("Stopping Application Resources...")
    from .core.database import engine
    service.stop()
    engine.dispose()
    logger.info("Application Shutdown Complete.")

app = FastAPI(
    title="AI Interview Platform API",
    description="High-performance JSON API for AI-driven face/gaze detection and automated interviews.",
    version="2.0.0",
    lifespan=lifespan,
    
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(candidate.router, prefix="/api")
