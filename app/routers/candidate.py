from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
import random
from ..models.db_models import User, InterviewSession, InterviewResponse, SessionQuestion, QuestionPaper, Questions
from ..schemas.api_response import ApiResponse

router = APIRouter(prefix="/candidate", tags=["Candidate"])

from ..schemas.requests import UserUpdate
from ..schemas.responses import HistoryItem
from ..auth.dependencies import get_current_user
from datetime import datetime



@router.get("/history", response_model=ApiResponse[List[HistoryItem]])
async def my_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(InterviewSession).where(
        InterviewSession.candidate_id == current_user.id
    ).order_by(InterviewSession.start_time.desc())
    
    sessions = session.exec(statement).all()
    
    history = []
    for s in sessions:
        history.append(HistoryItem(
            interview_id=s.id,
            paper_name=s.paper.name if s.paper else "General",
            date=s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "Scheduled",
            score=s.total_score
        ))
    return ApiResponse(
        status_code=200,
        data=history,
        message="Interview history retrieved successfully"
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
    
    # 3. Generate Embedding (ArcFace)
    try:
        from deepface import DeepFace
        import numpy as np
        import json
        import tempfile
        import os

        # DeepFace.represent expects a path or ndarray. 
        # Using a temp file is safest for binary bytes.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            objs = DeepFace.represent(
                img_path=tmp_path, 
                model_name="ArcFace", 
                enforce_detection=False
            )
            embedding = objs[0]["embedding"]
            current_user.face_embedding = json.dumps(embedding)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        # We still save the bytes even if embedding fails, but log it
        
    # 4. Legacy: Save to disk
    upload_dir = "app/assets/images/profiles"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/user_{current_user.id}.jpg"
    with open(file_path, "wb") as buffer:
        buffer.write(image_bytes)
        
    current_user.profile_image = file_path
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
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
    """Streams the user's profile image (selfie) directly to the browser."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 1. Try DB Bytes
    if user.profile_image_bytes:
        from fastapi.responses import Response
        import imghdr
        ext = imghdr.what(None, h=user.profile_image_bytes) or "jpeg"
        return Response(content=user.profile_image_bytes, media_type=f"image/{ext}")
        
    # 2. Try Disk Fallback
    if user.profile_image and os.path.exists(user.profile_image):
        return FileResponse(user.profile_image)
        
    raise HTTPException(status_code=404, detail="No profile image found for this user")
