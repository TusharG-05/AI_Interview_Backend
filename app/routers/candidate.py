from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
import random
from ..models.db_models import User, InterviewSession, InterviewResult, Answers, SessionQuestion, QuestionPaper, Questions, InterviewStatus
from ..schemas.api_response import ApiResponse

router = APIRouter(prefix="/candidate", tags=["Candidate"])

from ..schemas.requests import UserUpdate
from ..schemas.responses import HistoryItem
from ..auth.dependencies import get_current_user
from datetime import datetime
from ..utils import format_iso_datetime



@router.get("/history", response_model=ApiResponse[List[HistoryItem]])
async def my_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(InterviewSession).where(
        InterviewSession.candidate_id == current_user.id
    ).order_by(InterviewSession.schedule_time.desc())
    
    sessions = session.exec(statement).all()
    
    history = []
    for s in sessions:
        history.append(HistoryItem(
            interview_id=s.id,
            access_token=s.access_token,
            paper_name=s.paper.name if s.paper else "General",
            date=format_iso_datetime(s.start_time) if s.start_time else "Scheduled",
            status=s.status.value,
            score=s.total_score,
            duration_minutes=s.duration_minutes,
            max_questions=s.max_questions,
            start_time=format_iso_datetime(s.start_time) if s.start_time else None,
            end_time=format_iso_datetime(s.end_time) if s.end_time else None,
            warning_count=s.warning_count,
            is_completed=s.is_completed,
            current_status=s.current_status.value if s.current_status else None
        ))
    return ApiResponse(
        status_code=200,
        data=history,
        message="Interview history retrieved successfully"
    )

@router.get("/interviews", response_model=ApiResponse[List[HistoryItem]])
async def my_interviews(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Fetch scheduled and upcoming interviews for the candidate."""
    statement = select(InterviewSession).where(
        InterviewSession.candidate_id == current_user.id,
        InterviewSession.status == InterviewStatus.SCHEDULED
    ).order_by(InterviewSession.schedule_time.asc())
    
    sessions = session.exec(statement).all()
    
    interviews = []
    for s in sessions:
        interviews.append(HistoryItem(
            interview_id=s.id,
            access_token=s.access_token,
            paper_name=s.paper.name if s.paper else "General",
            date=format_iso_datetime(s.schedule_time) if s.schedule_time else "Scheduled",
            status=s.status.value,
            score=None,
            duration_minutes=s.duration_minutes,
            max_questions=s.max_questions,
            start_time=format_iso_datetime(s.start_time) if s.start_time else None,
            end_time=format_iso_datetime(s.end_time) if s.end_time else None,
            warning_count=s.warning_count,
            is_completed=s.is_completed,
            current_status=s.current_status.value if s.current_status else None
        ))
    return ApiResponse(
        status_code=200,
        data=interviews,
        message="Upcoming interviews retrieved successfully"
    )

import shutil
import os
from fastapi import UploadFile, File

@router.post("/upload-selfie", response_model=ApiResponse[dict])
async def upload_selfie(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Allows candidate to upload their reference selfie for face verification."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    # 1. Read bytes
    image_bytes = await file.read()
    
    # 2. Save to DB (Binary Store)
    current_user.profile_image_bytes = image_bytes
    
    # 3. Generate Dual Embeddings (Hybrid Strategy)
    try:
        from deepface import DeepFace
        import numpy as np
        import json
        import tempfile
        import os

        embeddings_map = {}
        
        # Using a temp file is safest for binary bytes.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            # 1. Generate ArcFace (High Accuracy - For Modal)
            try:
                from ..core.logger import get_logger
                logger = get_logger(__name__)
                logger.info("Generating ArcFace embedding...")
                arc_objs = DeepFace.represent(img_path=tmp_path, model_name="ArcFace", enforce_detection=False)
                if arc_objs:
                    embeddings_map["ArcFace"] = arc_objs[0]["embedding"]
            except Exception as e:
                logger.warning(f"ArcFace embedding failed: {e}")

            # 2. Generate SFace (Lightweight - For Local Fallback)
            try:
                logger.info("Generating SFace embedding...")
                sface_objs = DeepFace.represent(img_path=tmp_path, model_name="SFace", enforce_detection=False)
                if sface_objs:
                    embeddings_map["SFace"] = sface_objs[0]["embedding"]
            except Exception as e:
                logger.warning(f"SFace embedding failed: {e}")

            if embeddings_map:
                current_user.face_embedding = json.dumps(embeddings_map)
                logger.info(f"Generated embeddings for: {list(embeddings_map.keys())}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        from ..core.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Embedding generation failed: {e}")
        # We still save the bytes even if embedding fails, but log it
        
    # 4. Legacy: Save to disk
    upload_dir = "app/assets/images/profiles"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/user_{current_user.id}.jpg"
    with open(file_path, "wb") as buffer:
        buffer.write(image_bytes)
        
    current_user.profile_image = file_path
    session.add(current_user)
    
    try:
        session.commit()
        session.refresh(current_user)
    except Exception as e:
        session.rollback()
        from ..core.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to save profile image: {e}")
        raise HTTPException(status_code=500, detail="Failed to save profile image")
    
    return ApiResponse(
        status_code=200,
        data={
            "user_id": current_user.id,
            "profile_image_url": f"/api/candidate/profile-image/{current_user.id}"
        },
        message="Selfie uploaded and identity verified successfully"
    )

@router.get("/profile-image/{user_id}")
async def get_profile_image(
    user_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Streams the user's profile image (selfie) directly to the browser.
    
    Returns:
        - Raw image bytes with appropriate Content-Type header if image found
        - 404 if no image exists
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 1. Try DB Bytes (preferred storage location)
    if user.profile_image_bytes:
        from fastapi.responses import Response
        import imghdr
        ext = imghdr.what(None, h=user.profile_image_bytes) or "jpeg"
        return Response(
            content=user.profile_image_bytes, 
            media_type=f"image/{ext}",
            headers={"Content-Disposition": "inline"}
        )
        
    # 2. Try Disk Fallback
    if user.profile_image and os.path.exists(user.profile_image):
        return FileResponse(
            user.profile_image,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline"}
        )
        
    raise HTTPException(status_code=404, detail="No profile image found for this user")
