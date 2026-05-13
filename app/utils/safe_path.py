import os
from fastapi import HTTPException
from ..core.config import ASSETS_DIR, DEEPFACE_STORAGE_DIR

def validate_safe_path(requested_path: str, allowed_dirs: list = None) -> str:
    """
    Validates that a requested path is within the allowed directories.
    Prevents path traversal attacks (e.g., ../../../etc/passwd).
    """
    if not requested_path:
        raise HTTPException(status_code=400, detail="Path is required")
        
    if allowed_dirs is None:
        # Default allowed directories
        allowed_dirs = [
            os.path.abspath(ASSETS_DIR),
            os.path.abspath(DEEPFACE_STORAGE_DIR),
            os.path.abspath("temp"), # Allow local temp if any
            os.path.abspath(os.path.join(os.getcwd(), "app/assets"))
        ]
        # Also allow system temp directory for NamedTemporaryFile
        import tempfile
        allowed_dirs.append(os.path.abspath(tempfile.gettempdir()))

    # Convert to absolute path and resolve symlinks
    try:
        abs_requested = os.path.abspath(os.path.realpath(requested_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path format: {e}")
    
    # Check if requested path is inside any allowed dir
    is_safe = False
    for allowed_dir in allowed_dirs:
        abs_allowed = os.path.abspath(os.path.realpath(allowed_dir))
        if abs_requested.startswith(abs_allowed):
            is_safe = True
            break
            
    if not is_safe:
        from ..core.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"SECURITY ALERT: Blocked path traversal attempt to: {abs_requested}")
        raise HTTPException(status_code=403, detail="Access denied: Path outside allowed directory")
        
    return abs_requested
