from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
import logging
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
from ..schemas.auth.login import LoginRequest, TokenResponse as Token, MeResponse as UserRead
from ..schemas.auth.registration import RegisterRequest as UserCreate
from ..schemas.shared.api_response import ApiResponse
from ..schemas.shared.user import serialize_user

from typing import Optional
from ..auth.dependencies import get_current_user, get_current_user_optional
from ..models.db_models import User, UserRole, InterviewSession, InterviewStatus, Team
from ..services.email import EmailService
from ..services.interview_access import LINK_VALIDITY_MINUTES, evaluate_interview_access

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

# Initialize services
email_service = EmailService()

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

@router.post("/login", response_model=ApiResponse[dict])
async def login(response: Response, login_data: LoginRequest, session: Session = Depends(get_session)):
    """JSON-based login. Sets secure HttpOnly cookie and returns token."""
    user = session.exec(select(User).where(User.email == login_data.email.lower())).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        logger.error(f"Login failed for user: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # Enforce access_token requirement for candidates
    if user.role == UserRole.CANDIDATE:
        if not login_data.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Interview token is required for candidates.",
            )
        
        # Verify the interview session token matches the candidate
        
        interview = session.exec(
            select(InterviewSession).where(
                InterviewSession.access_token == login_data.access_token,
                InterviewSession.candidate_id == user.id
            )
        ).first()
        
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid interview link or candidate mismatch.",
            )

        access_decision = evaluate_interview_access(interview)
        if not access_decision.allowed:
            if access_decision.reason == "cancelled":
                raise HTTPException(status_code=403, detail="This interview has been cancelled.")
            if access_decision.reason == "completed":
                raise HTTPException(status_code=403, detail="This interview has already been completed.")
            if access_decision.entry_window_expired or access_decision.reason == "explicitly_expired":
                if interview.status != InterviewStatus.EXPIRED:
                    interview.status = InterviewStatus.EXPIRED
                    session.add(interview)
                    session.commit()
                raise HTTPException(
                    status_code=403,
                    detail=f"This interview link has expired. Candidates must join within {LINK_VALIDITY_MINUTES} minutes of the scheduled time.",
                )
            if access_decision.duration_expired:
                raise HTTPException(status_code=403, detail="This interview session has expired.")
            raise HTTPException(status_code=403, detail="Interview link is not active.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    set_auth_cookie(response, token)
    
    from .teams import _serialize_team_basic
    team_data = _serialize_team_basic(user.team, session) if user.team else None

    token_data = {
        "access_token": token, 
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": str(user.role.value) if hasattr(user.role, "value") else str(user.role),
        "profile_image" : user.profile_image,
        "team": team_data
    }
    print(token_data)
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
    user = session.exec(select(User).where(User.email == form_data.username.lower())).first()
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
    
    from .teams import _serialize_team_basic
    team_data = _serialize_team_basic(user.team, session) if user.team else None

    return {
        "access_token": token, 
        "token_type": "bearer",
        "id": user.id,
        "role": str(user.role.value) if hasattr(user.role, "value") else str(user.role),
        "email": user.email,
        "full_name": user.full_name,
        "expires_at": (datetime.now(timezone.utc) + access_token_expires).isoformat(),
        "team": team_data
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

@router.post("/register", response_model=ApiResponse[Token], status_code=201)
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
    # Bootstrap Check - first user can register freely
    all_user_count = len(session.exec(select(User)).all())
    
    if all_user_count > 0:
        # Require Admin Auth
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            logger.error(f"Unauthorized registration attempt by user: {current_user.email if current_user else 'None'}")
            raise HTTPException(
                status_code=403,
                detail="Registration is restricted to Admins. Please contact an administrator."
            )
        
        # Role-based restriction: Admins can only create Candidates
        if current_user.role == UserRole.ADMIN and user_data.role != UserRole.CANDIDATE:
            raise HTTPException(
                status_code=403,
                detail="Admins are only permitted to register Candidates. Please contact a Super Admin for other roles."
            )

    existing_user = session.exec(select(User).where(User.email == user_data.email.lower())).first()
    if existing_user:
        logger.error(f"Registration attempt for already registered email: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)

    # Handle Team assignment for new user
    team_id = user_data.team_id

    # Bootstrap: First user is SUPER_ADMIN
    if all_user_count == 0:
        user_data.role = UserRole.SUPER_ADMIN
        team_id = None

    new_user = User(
        email=user_data.email.lower(),
        full_name=user_data.full_name,
        password_hash=hashed_password,
        role=user_data.role,
        team_id=team_id
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
    
    from .teams import _serialize_team_basic
    team_data = _serialize_team_basic(new_user.team, session) if new_user.team else None

    token_data = {
        "access_token": token, 
        "token_type": "bearer",
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": str(new_user.role.value) if hasattr(new_user.role, "value") else str(new_user.role),
        "expires_at": expire_time.isoformat(),
        "team": team_data
    }
    
    return ApiResponse(
        status_code=201,
        data=token_data,
        message="User registered successfully"
    )

@router.get("/me", response_model=ApiResponse[dict])
async def read_users_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Get current logged in user details with complete profile information."""
    
    # Get complete user data
    user_data = serialize_user(current_user)
    
    # Add additional profile information
    user_data.update({
        "has_profile_image": current_user.profile_image_bytes is not None or current_user.profile_image is not None,
        "has_face_embedding": current_user.face_embedding is not None
    })

    # Ensure team is serialized correctly if present
    if current_user.team:
        from .teams import _serialize_team_basic
        user_data["team"] = _serialize_team_basic(current_user.team, session)
    
    return ApiResponse(
        status_code=200,
        data=user_data,
        message="User profile retrieved successfully"
    )
