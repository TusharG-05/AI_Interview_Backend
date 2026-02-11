import os
import shutil
import contextlib
from fastapi import FastAPI
from .core.database import init_db
from .core.logger import setup_logging, get_logger

# PRE-INIT: Database must be initialized before heavy AI imports (Torch/TensorFlow)
# to avoid segmentation faults in the database driver (psycopg2-binary).
setup_logging()
logger = get_logger(__name__)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Lifespan: Starting Application (API-Only Mode)...")
    
    # Ensure ffmpeg is available for local environments (port 8001)
    if not shutil.which("ffmpeg"):
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
            logger.info("Lifespan: static_ffmpeg initialized.")
        except ImportError:
            logger.warning("Lifespan: static_ffmpeg not installed on host.")

    logger.info("PRE-INIT: Initializing database...")
    init_db()
    
    # MONKEY PATCH: Fix speechbrain vs torchaudio 2.x incompatibility
    try:
        import torchaudio
        if not hasattr(torchaudio, "list_audio_backends"):
            logger.warning("Monkey Patching torchaudio.list_audio_backends for SpeechBrain")
            torchaudio.list_audio_backends = lambda: ["soundfile"]
    except ImportError:
        logger.warning("Torchaudio not found. Skipping monkey patch.")
    except Exception as e:
        logger.warning(f"Failed to apply torchaudio monkey patch: {e}")

    # These imports are now safe since init_db() already finished
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
    
    # Warm-up disabled for stability - enable via feature flag if needed
    # threading.Thread(target=warm_up, daemon=True).start()
    logger.info("Model warm-up: Deferred to first request for stability.")
    
    logger.info("Lifespan: Initializing CameraService...")
    service = CameraService()
    logger.info("Lifespan: Startup Complete.")
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

from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "path": request.url.path}
    )

from fastapi.middleware.cors import CORSMiddleware
import os

# SECURITY: Use environment-based CORS origins, never "*" with credentials
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (Redundant endpoint removed. Use settings.router instead)

# Lazy include routers to ensure AI models (imported within routers) 
# don't conflict with database initialization logic.
from .routers import video, settings, admin, interview, auth, candidate

app.include_router(video.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(candidate.router, prefix="/api")
