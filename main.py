from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.interview import router as interview_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.candidate import router as candidate_router
from config.database import create_db_and_tables

# Initialize FastAPI app
app = FastAPI(
    title="AI Interview Platform",
    description="Practice technical interviews with AI-powered questions"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(candidate_router)
app.include_router(interview_router)
