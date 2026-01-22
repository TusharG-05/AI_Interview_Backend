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
    service = CameraService()
    # service.start() is now lazy-loaded in video.py
    # to prevent camera access until frontend is opened.
    
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


