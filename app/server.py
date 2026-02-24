import os
import shutil
import contextlib
import sentry_sdk
from fastapi import FastAPI
from .core.database import init_db
from .core.logger import setup_logging, get_logger
from .core.config import SENTRY_DSN, REDIS_URL

# PRE-INIT: Database must be initialized before heavy AI imports (Torch/TensorFlow)
# to avoid segmentation faults in the database driver (psycopg2-binary).
setup_logging()
logger = get_logger(__name__)

# SENTRY: Professional Error Tracking
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Lifespan: Sentry monitoring initialized.")

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Lifespan: Starting Application (API-Only Mode)...")
    
    # RATE LIMITING: Protect AI resources
    try:
        import redis.asyncio as redis
        from fastapi_limiter import FastAPILimiter
        redis_conn = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_conn)
        logger.info("Lifespan: API Rate Limiting initialized (Redis).")
    except Exception as re_e:
        logger.warning(f"Lifespan: Rate Limiter failed to start: {re_e}")
    
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
        logger.info("Warm-up: Loading AI Models (Whisper, LLM, Speaker)...")
        from .core.config import local_llm
        try:
            # Trigger lazy loading properties for audio/speech models
            _ = audio_service.stt_model
            _ = audio_service.speaker_model
            
            # Local LLM (Ollama) is often absent in cloud/HF environments
            try:
                local_llm.invoke("Hello")
            except Exception as llm_e:
                logger.info(f"Warm-up: Local LLM (Ollama) unreachable, skipping pre-warm: {llm_e}")
                
            logger.info("Warm-up: AI Models Ready.")
        except Exception as e:
            logger.error(f"Warm-up process encountered an error: {e}")
    
    # Start warm-up in background thread so server starts instantly
    threading.Thread(target=warm_up, daemon=True).start()
    logger.info("Warm-up: Started in background thread for fast startup (Models: Whisper, LLM, Speaker).")
    
    logger.info("Lifespan: Initializing CameraService...")
    service = CameraService()
    service.start()  # ✅ CRITICAL: Start detectors for proctoring
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

from .schemas.api_response import ApiErrorResponse

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Catch 422 validation errors and wrap them."""
    return JSONResponse(
        status_code=422,
        content=ApiErrorResponse(
            status_code=422,
            message="Validation failed",
            data={"errors": jsonable_encoder(exc.errors())}
        ).model_dump()
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Catch global 404 errors (unmatched paths) and wrap them."""
    message = "Resource not found"
    if hasattr(exc, "detail"):
        message = str(exc.detail)
        
    return JSONResponse(
        status_code=404,
        content=ApiErrorResponse(
            status_code=404,
            message=message,
            data={"path": request.url.path}
        ).model_dump()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Catch other 4xx errors and wrap them."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(
            status_code=exc.status_code,
            message=str(exc.detail),
            data=None
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ApiErrorResponse(
            status_code=500,
            message="Internal Server Error",
            data={"path": request.url.path}
        ).model_dump()
    )

from fastapi.middleware.cors import CORSMiddleware
import os

# SECURITY: Allow ALL origins (including localhost) for development convenience
# WARNING: This effectively disables CORS protection.
# ALLOW_ORIGIN_REGEX = r".*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
