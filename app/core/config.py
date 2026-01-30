"""Configuration and settings for the application."""
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

# App Configuration
APP_TITLE = "Face/Gaze Aware AI Interview Platform"
APP_DESCRIPTION = "Advanced interview proctoring with AI-powered questions and evaluation."

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:3b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Initialize the local language model
local_llm = ChatOllama(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    base_url=OLLAMA_BASE_URL
)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local sqlite for dev ONLY if explicitly requested, otherwise fail or default to postgres service
    DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/interview_db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Security
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Fail-Fast in Production/Docker to prevent insecure defaults
    if os.getenv("ENV", "development") == "production":
         raise ValueError("FATAL: SECRET_KEY is missing in production environment.")
    print("WARNING: Using insecure default SECRET_KEY for development.")
    SECRET_KEY = "super-secret-key-change-in-production"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Assets and Paths
ASSETS_DIR = "app/assets"
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
PROCTORING_LOGS_DIR = os.path.join(ASSETS_DIR, "proctoring_logs")

# Ensure directories exist
for d in [ASSETS_DIR, AUDIO_DIR, PROCTORING_LOGS_DIR]:
    os.makedirs(d, exist_ok=True)
