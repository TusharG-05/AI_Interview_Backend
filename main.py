import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.interview import router as interview_router

# Initialize FastAPI app
app = FastAPI(
    title="AI Interview Platform",
    description="Practice technical interviews with AI-powered questions"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes
app.include_router(interview_router)