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
    
    # Fallback: Run in a separate thread to avoid blocking the event loop (since AI tasks are heavy)
    import threading
    logger.info(f"Task {task_func.__name__} starting in background thread (Celery disabled)...")
    thread = threading.Thread(target=task_func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return None
