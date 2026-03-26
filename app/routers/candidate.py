from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from ..core.database import get_db as get_session
import random
from ..models.db_models import User, InterviewSession, InterviewResult, Answers, SessionQuestion, QuestionPaper, Questions, InterviewStatus, CandidateStatus
from ..services.status_manager import record_status_change
from ..schemas.shared.api_response import ApiResponse

router = APIRouter(prefix="/candidate", tags=["Candidate"])

from ..schemas.admin.users import UserUpdate
from ..schemas.candidate.history import HistoryItem, ListUpcomingInterviewsResponse, UpcomingInterviewItem
from ..auth.dependencies import get_current_user
from ..core.logger import get_logger
logger = get_logger(__name__)
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
            current_status=s.current_status,
            allow_copy_paste=s.allow_copy_paste or False,
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
            total_score=s.total_score,
            duration_minutes=s.duration_minutes,
            max_questions=s.max_questions,
            start_time=format_iso_datetime(s.start_time) if s.start_time else None,
            end_time=format_iso_datetime(s.end_time) if s.end_time else None,
            warning_count=s.warning_count,
            is_completed=s.is_completed,
            current_status=s.current_status,
            allow_copy_paste=s.allow_copy_paste or False,
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
    interview_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Candidate uploads their own selfie for face enrollment and identity verification.
    Generates face embeddings (ArcFace + SFace) for proctoring during interview.
    Optionally updates interview status to SELFIE_UPLOADED if interview_id provided.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    # 1. Read bytes for processing
    image_bytes = await file.read()
    
    # 2. Update Interview Status if requested
    if interview_id:
        statement = select(InterviewSession).where(
            InterviewSession.id == interview_id,
            InterviewSession.candidate_id == current_user.id
        )
        interview_session = session.exec(statement).first()
        if interview_session:
            record_status_change(
                session=session,
                interview_session=interview_session,
                new_status=CandidateStatus.SELFIE_UPLOADED
            )
            logger.info(f"Updated status for interview {interview_id} to SELFIE_UPLOADED via candidate API")

    
        # 3. Generate Dual Embeddings (Hybrid Strategy)
    try:
        from deepface import DeepFace
        from ..services.face import USE_MODAL, get_modal_embedding
        import json
        import tempfile
        import os

        embeddings_map = {}
        
        # 1. Generate ArcFace (High Accuracy)
        # Try Modal.com if enabled
        if USE_MODAL:
            try:
                modal_cls = get_modal_embedding()
                if modal_cls:
                    logger.info("Calling Modal for ArcFace enrollment...")
                    result = modal_cls().get_embedding.remote(image_bytes)
                    if result.get("success"):
                        embeddings_map["ArcFace"] = result["embedding"]
                        logger.info("ArcFace embedding generated via Modal")
            except Exception as e:
                logger.warning(f"Modal ArcFace enrollment failed: {e}")

        # Fallback to local ArcFace if Modal failed/disabled
        if "ArcFace" not in embeddings_map:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                try:
                    arc_objs = DeepFace.represent(img_path=tmp_path, model_name="ArcFace", enforce_detection=False)
                    if arc_objs:
                        embeddings_map["ArcFace"] = arc_objs[0]["embedding"]
                        logger.info("ArcFace embedding generated locally")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"Local ArcFace fallback failed: {e}")

        # 2. Generate SFace (Always local as lightweight backup)
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            try:
                sface_objs = DeepFace.represent(img_path=tmp_path, model_name="SFace", enforce_detection=False)
                if sface_objs:
                    embeddings_map["SFace"] = sface_objs[0]["embedding"]
                    logger.info("SFace embedding generated locally")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            logger.warning(f"SFace embedding failed: {e}")

        if embeddings_map:
            current_user.face_embedding = json.dumps(embeddings_map)
            logger.info(f"Generated embeddings for: {list(embeddings_map.keys())}")
                
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        
    # 4. Finalize
    current_user.profile_image_bytes = image_bytes
    session.add(current_user)
    
    try:
        session.commit()
        session.refresh(current_user)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save profile embeddings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save profile embeddings")
    
    return ApiResponse(
        status_code=200,
        data={
            "user_id": current_user.id,
            "has_embeddings": current_user.face_embedding is not None,
            "status_updated": interview_id is not None
        },
        message="Selfie identity verified and embeddings generated successfully"
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
        
    # 2. Try URL (Cloudinary)
    if user.profile_image and user.profile_image.startswith("http"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=user.profile_image)

    # 3. Try Disk Fallback
    if user.profile_image and os.path.exists(user.profile_image):
        return FileResponse(
            user.profile_image,
            media_type="image/jpeg",
            headers={"Content-Disposition": "inline"}
        )
        
    raise HTTPException(status_code=404, detail="No profile image found for this user")
