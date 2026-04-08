from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request, WebSocket, Query
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole
from .security import SECRET_KEY, ALGORITHM
from ..core.logger import get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    logger.info(f"DEBUG AUTH: get_current_user START. Token exists: {token is not None}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try getting token from cookie if header is missing
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        raise credentials_exception

    try:
        logger.info(f"DEBUG: Decoding token starting: {token[:20]}... with key starting: {SECRET_KEY[:5]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Only SUPER_ADMIN can pass. Admin and below are rejected."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins are allowed to perform this action"
        )
    return current_user

def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> Optional[User]:
    """Returns current user if authenticated, else None."""
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    
    user = session.query(User).filter(User.email == email).first()
    return user

async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    session: Session = Depends(get_session)
) -> User:
    """Validate current user for WebSocket connections."""
    if not token:
        token = websocket.cookies.get("access_token")
        
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token missing")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = session.query(User).filter(User.email == email).first()
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    return user

async def get_admin_user_ws(current_user: User = Depends(get_current_user_ws)) -> User:
    """Ensure the WebSocket user is an admin."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        # Note: We can't easily close from here if we want to return the user, 
        # but the endpoint can check the role or we can raise and let FastAPI handle it.
        # However, for WS, it's better to be explicit.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user
