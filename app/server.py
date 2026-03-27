import os
import shutil
import contextlib
import sentry_sdk
from typing import Any
from fastapi import FastAPI
from fastapi.routing import APIRouter, APIRoute
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

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
from .core.config import SENTRY_DSN, REDIS_URL

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

# logger.info("PRE-INIT: Initializing database...")
# init_db()

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
        logger.info("Lifespan: API Rate Limiting initialized successfully.")
    except ImportError:
        logger.warning("Lifespan: fastapi-limiter not installed. Rate limiting disabled.")
    except Exception as re_e:
        logger.error(f"Lifespan: Rate Limiter failed to start: {re_e}")
    
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
    # On HF Spaces, we skip local ML warmup to save memory and startup time
    if not os.getenv("SPACE_ID"):
        threading.Thread(target=warm_up, daemon=True).start()
        logger.info("Warm-up: Started in background thread for fast startup (Models: Whisper, LLM, Speaker).")
    else:
        logger.info("Warm-up: Skipped local model pre-warm on Hugging Face Space.")
    
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
    default_response_class=ExcludeNoneJSONResponse,
    route_class=ExcludeNoneRoute,
)

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

@app.middleware("http")
async def diagnostic_logging_middleware(request: Request, call_next):
    # Skip in production/Hugging Face to avoid issues
    if os.getenv("ENV") == "production" or os.getenv("SPACE_ID"):
        return await call_next(request)
        
    # Skip noisy endpoints like swagger docs
    if request.url.path in ["/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
        
    start_time = time.time()
    
    # 1. Safely read and restore the request body (Skip multipart to avoid breaking file uploads)
    content_type = request.headers.get("content-type", "")
    is_multipart = "multipart/form-data" in content_type
    
    body_str = ""
    is_json = False
    
    if not is_multipart:
        try:
            body_bytes = await request.body()
            # Restore the stream so the endpoints can still access the body
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
            
            # 2. Try to parse JSON for pretty printing and masking passwords
            if body_bytes:
                try:
                    parsed = json.loads(body_bytes)
                    # Mask potential secrets
                    for key in ["password", "token", "access_token"]:
                        if isinstance(parsed, dict) and key in parsed:
                            parsed[key] = "********"
                    body_str = json.dumps(parsed, indent=2)
                    is_json = True
                except Exception:
                    body_str = body_bytes.decode(errors="replace")[:500]
        except Exception:
            body_str = "<error reading body>"
    else:
        body_str = "<multipart/form-data (skipped to preserve stream)>"

    print(f"\n\033[96m[REQUEST START] {request.method} {request.url.path}\033[0m", flush=True)
    if body_str:
        print(f"\033[90mPayload:\n{body_str}\033[0m", flush=True)
        
    # 3. Execute the request and catch any 500s directly here to print context
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Color based on status code
        if 200 <= response.status_code < 300:
            color = "\033[92m" # Green
        elif 400 <= response.status_code < 500:
            color = "\033[93m" # Yellow
        else:
            color = "\033[91m" # Red
            
        print(f"{color}[REQUEST END] {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms\033[0m", flush=True)
        return response
        
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        print(f"\n\033[91m====================== CRITICAL ERROR ======================\033[0m", flush=True)
        print(f"\033[91mFailed Endpoint: {request.method} {request.url.path}\033[0m", flush=True)
        print(f"\033[91mExecution Time: {process_time:.2f}ms\033[0m", flush=True)
        print(f"\033[91mInput Payload that caused failure:\n{body_str}\033[0m", flush=True)
        print(f"\033[91m------------------------------------------------------------\033[0m", flush=True)
        import traceback
        traceback.print_exc()
        print(f"\033[91m============================================================\033[0m\n", flush=True)
        raise e

# (Redundant endpoint removed. Use settings.router instead)

# Lazy include routers to ensure AI models (imported within routers) 
# don't conflict with database initialization logic.
from .routers import video, settings, admin, interview, auth, candidate, teams, coding_papers, resume

app.include_router(video.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(interview.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(candidate.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(coding_papers.router, prefix="/api")
app.include_router(resume.router, prefix="/api")

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
