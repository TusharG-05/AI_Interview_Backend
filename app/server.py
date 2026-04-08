import os
import shutil
import contextlib
import sentry_sdk
from typing import Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRouter, APIRoute
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# --- Startup Instrumentation ---
print("\033[94m[STARTUP] app.server module initializing...\033[0m", flush=True)

class ExcludeNoneJSONResponse(JSONResponse):
    """Custom JSONResponse that excludes None values by default."""
    def render(self, content: Any) -> bytes:
        return super().render(jsonable_encoder(content, exclude_none=True))

class ExcludeNoneRoute(APIRoute):
    """Custom route class that excludes None values from responses by default."""
    def __init__(self, *args, **kw):
        if "response_model_exclude_none" not in kw:
            kw["response_model_exclude_none"] = True
        super().__init__(*args, **kw)

# Patch APIRouter globally so all routers (including those imported later) use this route class
APIRouter.route_class = ExcludeNoneRoute
from .core.database import init_db
from .core.logger import setup_logging, get_logger
from .core.config import SENTRY_DSN, REDIS_URL, IS_ORCHESTRATOR


# PRE-INIT: Database must be initialized before heavy AI imports (Torch/TensorFlow)
# to avoid segmentation faults in the database driver (psycopg2-binary).
setup_logging()
logger = get_logger(__name__)

# Ensure ffmpeg is available for local environments
if not shutil.which("ffmpeg"):
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
        logger.info("PRE-INIT: static_ffmpeg initialized.")
    except ImportError:
        logger.warning("PRE-INIT: static_ffmpeg not installed on host.")

logger.info("PRE-INIT: Initializing database...")
init_db()

# SENTRY: Professional Error Tracking
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Lifespan: Sentry monitoring initialized.")

def _apply_torchaudio_patch():
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

def _warm_up_ml_models():
    import time as _time
    # HF Space Fix: Skip pre-warm during launch to avoid 503 timeout
    if os.getenv("SPACE_ID"):
        logger.info("Warm-up: Skipping intensive local model pre-warm on Hugging Face Space for fast startup.")
        return

    # Wait slightly before starting heavy work to allow health check to pass
    _time.sleep(60) 
    logger.info("Warm-up: Loading AI Models (Whisper, LLM, Speaker)...")
    from .core.config import local_llm
    from .routers.interview import get_audio_service
    try:
        audio_service = get_audio_service()
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
        logger.info("Lifespan: API Rate Limiting initialized successfully.")
    except ImportError:
        logger.warning("Lifespan: fastapi-limiter not installed. Rate limiting disabled.")
    except Exception as re_e:
        logger.error(f"Lifespan: Rate Limiter failed to start: {re_e}")
    # --- Skip heavy ML if Orchestrator Mode ---
    if not IS_ORCHESTRATOR:
        _apply_torchaudio_patch()

        # These imports are now safe since init_db() already finished
        from .services.camera import CameraService
        import threading
        
        # Start warm-up in background thread so server starts instantly
        # On HF Spaces, we skip local ML warmup to save memory and startup time
        if not os.getenv("SPACE_ID"):
            threading.Thread(target=_warm_up_ml_models, daemon=True).start()
            logger.info("Warm-up: Started in background thread for fast startup (Models: Whisper, LLM, Speaker).")
        else:
            logger.info("Warm-up: Skipped local model pre-warm on Hugging Face Space.")
        
        logger.info("Lifespan: Initializing CameraService...")
        service = CameraService()
        service.start()  # ✅ CRITICAL: Start detectors for proctoring
    else:
        logger.info("Lifespan: Running in ORCHESTRATOR mode (ML Services disabled).")
        service = None
    
    logger.info("Lifespan: Startup Complete.")
    yield
    
    logger.info("Stopping Application Resources...")
    from .core.database import engine
    if service is not None:
        service.stop()
    engine.dispose()
    logger.info("Application Shutdown Complete.")

app = FastAPI(
    title="AI Interview Platform API",
    description="High-performance JSON API for AI-driven face/gaze detection and automated interviews.",
    version="2.0.0",
    lifespan=lifespan,
    default_response_class=ExcludeNoneJSONResponse,
    route_class=ExcludeNoneRoute,
)

# MOUNT: Serve local assets (Failover storage for stateless cloud dependencies)
os.makedirs("app/assets/audio/failover", exist_ok=True)
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

from fastapi.responses import JSONResponse
from fastapi.requests import Request

from .schemas.shared.api_response import ApiErrorResponse

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Catch 422 validation errors and wrap them."""
    return ExcludeNoneJSONResponse(
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
        
    return ExcludeNoneJSONResponse(
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
    message = str(exc.detail)
    data = None
    
    if isinstance(exc.detail, dict):
        # If detail is a dict, we pull out message and use the whole dict as data
        message = exc.detail.get("message", "Error occurred")
        data = exc.detail

    return ExcludeNoneJSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(
            status_code=exc.status_code,
            message=message,
            data=data
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}", exc_info=True)
    return ExcludeNoneJSONResponse(
        status_code=500,
        content=ApiErrorResponse(
            status_code=500,
            message="Internal Server Error",
            data={"path": request.url.path}
        ).model_dump()
    )

from .core.config import FRONTEND_URL
from fastapi.middleware.cors import CORSMiddleware

# SECURITY: Restrict origins in production, allow development origins
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if FRONTEND_URL:
    if FRONTEND_URL not in origins:
        origins.append(FRONTEND_URL)
if os.getenv("ENV") == "development":
    origins = ["*"] # Keep wildcard for local dev convenience if explicitly set

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HF Proxy Fix: Support X-Forwarded-Proto and X-Forwarded-For
# This ensures that WebSockets and Redirects use the correct protocol (https)
from fastapi import Request
try:
    from uvloop import install as uvloop_install
    uvloop_install()
    logger.info("PRE-INIT: uvloop installed.")
except ImportError:
    pass

@app.middleware("http")
async def proxy_fix_middleware(request: Request, call_next):
    # Hugging Face and other proxies send X-Forwarded-Proto
    # If it's https, we want to make sure the request's scope reflects that
    # so that redirects and link generations (like for WebSockets) are correct.
    proto = request.headers.get("x-forwarded-proto")
    if proto == "https":
        request.scope["scheme"] = "https"
    
    response = await call_next(request)
    return response

import time
import json


# --- Rate Limiting Strategy ---
from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

# 1. Global / General Limit (for lightweight APIs)
general_limiter = [Depends(RateLimiter(times=100, seconds=60))]
# 2. Auth Limit (Stricter to prevent brute force)
auth_limiter = [Depends(RateLimiter(times=20, seconds=60))]
# 3. Proctoring / Heartbeat Limit (Allow 2 req/sec for status/pings)
heavy_ai_limiter = [Depends(RateLimiter(times=120, seconds=60))]
# 4. Ultra-Heavy ML Tasks (Paper generation, result processing)
ml_task_limiter = [Depends(RateLimiter(times=10, seconds=60))]

# --- Router Inclusion (Instrumented for Cloud Debugging) ---
print("\n\033[94m[STARTUP] Loading routers...\033[0m", flush=True)

# Diagnostic
from .core.config import SECRET_KEY as C_SEC
from .auth.security import SECRET_KEY as S_SEC
print(f"DEBUG AUTH: Match={C_SEC == S_SEC} Config={C_SEC[:5]} Security={S_SEC[:5]}")

from .routers import auth, settings, admin, teams, coding_papers, resume, interview, candidate, video, admin_ws

print("\033[94m[STARTUP] Including Auth, Settings, Admin, Teams...\033[0m", flush=True)
app.include_router(auth.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(teams.router, prefix="/api")

print("\033[94m[STARTUP] Including Resume, Coding, Interview...\033[0m", flush=True)
app.include_router(resume.router, prefix="/api")
app.include_router(coding_papers.router, prefix="/api")
app.include_router(interview.router, prefix="/api")

print("\033[94m[STARTUP] Including Candidate Router...\033[0m", flush=True)
app.include_router(candidate.router, prefix="/api")

print("\033[94m[STARTUP] Including Video Router (Heavy)...\033[0m", flush=True)
app.include_router(video.router, prefix="/api")

# Heavy ML Routers: Only load if not in orchestrator-only mode
if IS_ORCHESTRATOR:
    logger.info("Orchestrator Mode: ML services are disabled but routers are active.")
else:
    pass

# General Dashboard Websocket (Real-time monitoring)
app.include_router(admin_ws.router, prefix="/api")

print("\033[92m[STARTUP] All routers included successfully.\033[0m\n", flush=True)

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
