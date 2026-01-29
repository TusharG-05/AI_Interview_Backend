from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.interview import router as interview_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.video import router as video_router
from routes.candidate import router as candidate_router
from config.database import create_db_and_tables


# Initialize FastAPI app
app = FastAPI(
    title="AI Interview Platform",
    description="Practice technical interviews with AI-powered questions"
)

# CORS Configuration
origins = ["*"]  # Allow all origins for development, can be restricted in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Mount static files
# Root endpoint (JSON)
@app.get("/")
async def root():
    return {"message": "AI Interview Platform API is running"}

# Include routes
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(video_router)
app.include_router(candidate_router)
app.include_router(interview_router)
import uvicorn
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    # Ensure spawn method is used (default on Windows, but good to be explicit for stability)
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
        
    print("Starting Server in STABLE mode (Reload Disabled for camera stability)...")
    
    import os
    import socket
    import shutil
    
    # Ensure ffmpeg is available for pydub
    if not shutil.which("ffmpeg"):
        import static_ffmpeg
        static_ffmpeg.add_paths()
    
    # Get local IP for easier connecting
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    ssl_config = {}
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        print(f"\n[SECURE MODE] SSL Certificates found.")
        print(f" -> Access from your laptop at: https://{local_ip}:8000")
        print(f" -> Access from your laptop at: https://0.0.0.0:8000 (if IP dynamic)")
        ssl_config = {
            "ssl_keyfile": "key.pem",
            "ssl_certfile": "cert.pem"
        }
    else:
        print("\n[WARNING] No SSL Certificates found. Camera/Mic will ONLY work on localhost.")
        print(" -> Run `python tools/generate_cert.py` to enable remote access.")

    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False, **ssl_config)
