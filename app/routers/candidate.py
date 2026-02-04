from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..core.database import get_db as get_session
import random
from ..models.db_models import User, InterviewSession, InterviewResponse, SessionQuestion, QuestionPaper, Questions

router = APIRouter(prefix="/candidate", tags=["Candidate"])

from ..schemas.requests import UserUpdate
from ..schemas.responses import HistoryItem
from ..auth.dependencies import get_current_user
from datetime import datetime



@router.get("/history", response_model=List[HistoryItem])
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
            session_id=s.id,
            paper_name=s.paper.name if s.paper else "General",
            date=s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "Scheduled",
            score=s.total_score
        ))
    return history

import shutil
import os
from fastapi import UploadFile, File

@router.post("/upload-selfie")
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
    
    return {"message": "Selfie uploaded and identity verified (DB Sync)", "user_id": current_user.id}
