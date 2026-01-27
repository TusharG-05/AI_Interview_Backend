import contextlib
import os
from fastapi import FastAPI
from .routers import video, site, settings, admin, interview
from .core.database import init_db

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting Application...")
    # Initialize database
    init_db()
    
    from .services.camera import CameraService
    from .routers.interview import audio_service, nlp_service
    
    # Pre-warm models in background to avoid blocking server start
    import threading
    def warm_up():
        print("Warm-up: Loading AI Models (Whisper, NLP)...")
        _ = audio_service.stt_model
        _ = nlp_service.model
        print("Warm-up: AI Models Ready.")
    
    threading.Thread(target=warm_up, daemon=True).start()
    
    service = CameraService()
    
    yield
    
    # Shutdown
    print("Stopping CameraService...")
    service.stop()

app = FastAPI(lifespan=lifespan)

app.include_router(site.router)
app.include_router(video.router)
app.include_router(settings.router)
app.include_router(admin.router)
app.include_router(interview.router)


