from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole
from .security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
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
