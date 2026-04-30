"""Configuration and settings for the application."""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

# App Configuration
APP_TITLE = "Face/Gaze Aware AI Interview Platform"
APP_DESCRIPTION = "Advanced interview proctoring with AI-powered questions and evaluation."

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:3b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Orchestrator & Environment Mode
ENV_MODE = os.getenv("ENV_MODE", "full")
IS_ORCHESTRATOR = ENV_MODE == "orchestrator"
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"

# Lazy-loaded LLM Initialization
_local_llm = None

def get_local_llm():
    """Lazy initialization for local LLM to save memory on startup."""
    global _local_llm
    if _local_llm is None:
        from langchain_ollama import ChatOllama
        _local_llm = ChatOllama(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            base_url=OLLAMA_BASE_URL
        )
    return _local_llm

# Legacy support for existing imports
# Note: Initializing it as a Proxy-like object OR just updating imports is better.
# For now, we'll keep the name but wrap it or update usages.
class LazyLLM:
    def __getattr__(self, name):
        return getattr(get_local_llm(), name)
    
    def __or__(self, other):
        # Support LangChain pipe operator (prompt | llm)
        return other | get_local_llm()
    
    def __ror__(self, other):
        # Support LangChain pipe operator (llm | output_parser)
        return get_local_llm() | other
    
    def invoke(self, input_data, config=None, **kwargs):
        # Support direct invocation
        return get_local_llm().invoke(input_data, config=config, **kwargs)
    
    def __call__(self, *args, **kwargs):
        # Support callable interface
        return get_local_llm()(*args, **kwargs)

local_llm = LazyLLM()



# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local sqlite for dev ONLY if explicitly requested, otherwise fail or default to postgres service
    # Default to localhost for non-docker environments
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/interview_db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Security
# Security
SECRET_KEY = os.getenv("SECRET_KEY")
ENV = os.getenv("ENV", "development")

if not SECRET_KEY:
    if ENV == "production":
        # FATAL: Never allow production start without secret
        raise ValueError("CRITICAL SECURITY ERROR: SECRET_KEY is missing in production environment.")
    else:
        # Dev: Generate random key instead of using predictable default
        import secrets
        logger = logging.getLogger("uvicorn")
        SECRET_KEY = secrets.token_urlsafe(32)
        logger.warning(f"Generated random SECRET_KEY for development: {SECRET_KEY[:10]}...")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Email Configuration
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "tushar@chicmicstudios.in")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", os.getenv("MAIL_FROM_EMAIL", ""))
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "AI Interview Platform")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true" or SMTP_PORT == 465

# Assets and Paths
ASSETS_DIR = "app/assets"
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
PROCTORING_LOGS_DIR = os.path.join(ASSETS_DIR, "proctoring_logs")

# Cloud Configuration
# Try to detect HF Direct URL or use Space URL as fallback
HF_SPACE_URL = os.getenv("HF_SPACE_URL", "https://huggingface.co/spaces/ichigo253/AI_Interview_Backend")
# For HF Spaces, the direct URL is username-space-name.hf.space
# But we'll trust APP_BASE_URL if manually set in secrets
APP_BASE_URL = os.getenv("APP_BASE_URL", HF_SPACE_URL)

# Frontend Configuration for Email Links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Sentry & Redis (for Rate Limiting)
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cloudinary Configuration
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Cron authentication secret for manual/externally-scheduled tasks
CRON_SECRET = os.getenv("CRON_SECRET", "")

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# Configure DeepFace to use project-local storage
# DeepFace will look for models in {DEEPFACE_HOME}/.deepface/weights
# In production (like HF Spaces), use /tmp for writable storage
if ENV == "production" or os.path.exists("/app"):
    DEEPFACE_STORAGE_DIR = "/tmp/deepface"
else:
    # Local dev
    DEEPFACE_STORAGE_DIR = os.path.abspath("models/deepface")
    
os.environ["DEEPFACE_HOME"] = DEEPFACE_STORAGE_DIR
try:
    os.makedirs(DEEPFACE_STORAGE_DIR, exist_ok=True)
except Exception as e:
    # Last resort fallback to /tmp
    DEEPFACE_STORAGE_DIR = "/tmp/deepface"
    os.environ["DEEPFACE_HOME"] = DEEPFACE_STORAGE_DIR
    os.makedirs(DEEPFACE_STORAGE_DIR, exist_ok=True)

# Ensure directories exist
for d in [ASSETS_DIR, AUDIO_DIR, PROCTORING_LOGS_DIR]:
    os.makedirs(d, exist_ok=True)