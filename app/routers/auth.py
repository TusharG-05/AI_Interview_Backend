from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from ..core.database import get_db as get_session
from ..models.db_models import User
from ..auth.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..schemas.requests import UserCreate, LoginRequest
from ..schemas.responses import Token


router = APIRouter(prefix="/auth", tags=["Authentication"])

def set_auth_cookie(response: Response, token: str):
    """Sets the access_token cookie with secure flags."""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=True  # Ensure this is True in production (HTTPS)
    )

@router.post("/login", response_model=Token)
async def login(response: Response, login_data: LoginRequest, session: Session = Depends(get_session)):
    """JSON-based login. Sets secure HttpOnly cookie and returns token."""
    user = session.query(User).filter(User.email == login_data.email).first()
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
    
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "expires_at": expire_time.isoformat()
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Standard OAuth2 token endpoint for Swagger UI (Authorize button)."""
    user = session.query(User).filter(User.email == form_data.username).first()
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
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat()
    }

@router.post("/logout")
async def logout(response: Response):
    """Clears the authentication cookie."""
    response.delete_cookie(key="access_token", samesite="lax", secure=True)
    return {"message": "Logged out successfully"}

@router.post("/register", response_model=Token)
async def register(response: Response, user_data: UserCreate, session: Session = Depends(get_session)):
    """Pure API registration. Sets secure HttpOnly cookie and returns token."""
    existing_user = session.query(User).filter(User.email == user_data.email).first()
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
    
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "role": new_user.role,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "expires_at": expire_time.isoformat()
    }
