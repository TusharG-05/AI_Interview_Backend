from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Get broker URL from environment or default to local Redis
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "interview_platform",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks.email_tasks", "app.tasks.interview_tasks"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max for heavy AI tasks
    broker_connection_timeout=3.0, # Fail fast if Redis is unreachable (API blocking)
    broker_connection_retry_on_startup=False,
)

if __name__ == "__main__":
    celery_app.start()
