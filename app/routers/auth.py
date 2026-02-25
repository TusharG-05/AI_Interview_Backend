from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User
from ..auth.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..schemas.requests import UserCreate, LoginRequest
from ..schemas.responses import Token, UserRead
from ..schemas.api_response import ApiResponse
from typing import Optional
from ..auth.dependencies import get_current_user, get_current_user_optional
from ..models.db_models import User, UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])

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

@router.post("/login", response_model=ApiResponse[Token])
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
    expire_time = datetime.now(timezone.utc) + access_token_expires
    
    token_data = {
        "access_token": token, 
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "expires_at": expire_time.isoformat()
    }
    
    return ApiResponse(
        status_code=200,
        data=token_data,
        message="Login successfully"
    )

@router.post("/token", response_model=Token)
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
        "expires_at": (datetime.now(timezone.utc) + access_token_expires).isoformat()
    }

@router.post("/logout", response_model=ApiResponse[dict])
async def logout(response: Response):
    """Clears the authentication cookie."""
    from ..core.config import ENV
    response.delete_cookie(key="access_token", samesite="lax", secure=(ENV == "production"))
    return ApiResponse(
        status_code=200,
        data={},
        message="Logged out successfully"
    )

@router.post("/register", response_model=ApiResponse[Token])
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
    
    try:
        session.commit()
        session.refresh(new_user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to register user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    
    set_auth_cookie(response, token)
    expire_time = datetime.now(timezone.utc) + access_token_expires
    
    token_data = {
        "access_token": token, 
        "token_type": "bearer",
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "expires_at": expire_time.isoformat()
    }
    
    return ApiResponse(
        status_code=201,
        data=token_data,
        message="User registered successfully"
    )

@router.get("/me", response_model=ApiResponse[dict])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current logged in user details with complete profile information."""
    from ..schemas.user_schemas import serialize_user
    
    # Get complete user data
    user_data = serialize_user(current_user)
    
    # Add additional profile information
    user_data.update({
        "has_profile_image": current_user.profile_image_bytes is not None or current_user.profile_image is not None,
        "has_face_embedding": current_user.face_embedding is not None,
        "resume_text": current_user.resume_text
    })
    
    return ApiResponse(
        status_code=200,
        data=user_data,
        message="User profile retrieved successfully"
    )

