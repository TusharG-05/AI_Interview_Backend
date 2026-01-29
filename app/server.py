import contextlib
import os
from fastapi import FastAPI
from .routers import video, site, settings, admin, interview, auth, candidate
from .core.database import init_db
from .core.logger import setup_logging, get_logger

logger = get_logger(__name__)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting Application...")
    # Initialize database
    init_db()
    
    from .services.camera import CameraService
    from .routers.interview import audio_service, nlp_service
    
    # Pre-warm models in background to avoid blocking server start
    import threading
    def warm_up():
        logger.info("Warm-up: Loading AI Models (Whisper, LLM)...")
        from .core.config import local_llm
        try:
            _ = audio_service.stt_model
            # Warm up LLM with a simple prompt
            local_llm.invoke("Hello")
            logger.info("Warm-up: AI Models Ready.")
        except Exception as e:
            logger.error(f"Warm-up failed: {e}")
    
    threading.Thread(target=warm_up, daemon=True).start()
    
    service = CameraService()
    
    yield
    
    # Shutdown
    logger.info("Stopping CameraService...")
    service.stop()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(site.router)
app.include_router(video.router)
app.include_router(settings.router)
app.include_router(admin.router)
app.include_router(interview.router)
app.include_router(auth.router)
app.include_router(candidate.router)

# Mount static files for the new UI
from fastapi.staticfiles import StaticFiles
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")
app.mount("/static", StaticFiles(directory="app/assets"), name="static")
