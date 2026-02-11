from datetime import timedelta, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole
from ..auth.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..schemas.requests import UserCreate, LoginRequest
from ..schemas.responses import Token, UserRead
from ..schemas.api_response import ApiResponse
from ..utils.response_helpers import StandardizedRoute
from ..auth.dependencies import get_current_user, get_current_user_optional

router = APIRouter(prefix="/auth", tags=["Authentication"], route_class=StandardizedRoute)

def set_auth_cookie(response: Response, token: str):
    """Sets the access_token cookie with secure flags."""
    from ..core.config import ENV
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=(ENV == "production")  # Only secure in production (HTTPS)
    )

@router.post("/login")
async def login(response: Response, login_data: LoginRequest, session: Session = Depends(get_session)):
    """JSON-based login. Sets secure HttpOnly cookie and returns token."""
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    set_auth_cookie(response, token)
    expire_time = datetime.utcnow() + access_token_expires
    
    token_data = {
        "access_token": token, 
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "expires_at": expire_time.isoformat()
    }
    
    return {"message": "Login successful", "data": token_data}

@router.post("/token")
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Standard OAuth2 token endpoint for Swagger UI (Authorize button)."""
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    set_auth_cookie(response, token)
    return {
        "access_token": token, 
        "token_type": "bearer",
        "id": user.id,
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat()
    }

@router.post("/logout")
async def logout(response: Response):
    """Clears the authentication cookie."""
    from ..core.config import ENV
    response.delete_cookie(key="access_token", samesite="lax", secure=(ENV == "production"))
    return {"message": "Logged out successfully"}

@router.post("/register")
async def register(
    response: Response, 
    user_data: UserCreate, 
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Register a new user. 
    - First user can register freely (Bootstrap).
    - Subsequent users must be registered by an Admin.
    """
    # Bootstrap Check
    user_count = len(session.exec(select(User)).all())
    if user_count > 0:
        # Require Admin Auth
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=403, 
                detail="Registration is restricted to Admins. Please contact an administrator."
            )

    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hashed_password,
        role=user_data.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    
    set_auth_cookie(response, token)
    expire_time = datetime.utcnow() + access_token_expires
    
    token_data = {
        "access_token": token, 
        "token_type": "bearer",
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "expires_at": expire_time.isoformat()
    }
    
    return {"message": "User registered successfully", "data": token_data}

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current logged in user details."""
    return {"message": "User details retrieved successfully", "data": current_user}

