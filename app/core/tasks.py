import logging
import os
from .config import IS_ORCHESTRATOR

logger = logging.getLogger(__name__)

def run_background_task(task_func, *args, **kwargs):
    """
    Decides whether to run a task via Celery or FastAPI BackgroundTasks.
    On Render Free Tier (Orchestrator Mode), we use BackgroundTasks to save memory.
    """
    use_celery = not IS_ORCHESTRATOR and os.getenv("DISABLE_CELERY", "false").lower() == "false"
    
    if use_celery:
        try:
            # Try to use Celery delay if it's a celery task object
            if hasattr(task_func, "delay"):
                logger.info(f"Dispatching task {task_func.__name__} to Celery...")
                return task_func.delay(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Celery dispatch failed, falling back to synchronous execution: {e}")
    
    # Fallback/Default: Run via BackgroundTasks (provided by the router)
    # Note: The caller must have access to background_tasks: BackgroundTasks
    logger.info(f"Task {task_func.__name__} will be handled via BackgroundTasks or Direct Call.")
    return task_func(*args, **kwargs)
