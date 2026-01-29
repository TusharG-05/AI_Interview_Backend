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
