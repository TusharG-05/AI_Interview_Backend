 
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from sqlmodel import Session, select
from ..core.database import get_db as get_session
from ..models.db_models import User, UserRole
from ..auth.dependencies import get_current_user

from ..schemas.shared.api_response import ApiResponse
from ..schemas.resume.extract import ResumeResponse

router = APIRouter(prefix="/resume", tags=["Resume Management"])
from ..auth.dependencies import get_current_user_optional
from ..models.db_models import InterviewSession
import os
import requests
import tempfile

_nlp_service = None

def get_nlp_service():
    global _nlp_service
    if _nlp_service is None:
        from ..services.nlp import NLPService
        _nlp_service = NLPService()
    return _nlp_service

@router.get("/", response_model=ApiResponse[ResumeResponse])
async def get_resume(
    user_id: Optional[int] = None,
    interview_token: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    """
    Retrieve resume metadata for specified user_id or current user.
    Admins can retrieve any, users only their own.
    Allows access via interview_token for candidates.
    """
    # 1. Resolve target_user_id
    target_user_id = user_id
    
    if interview_token:
        # Validate token and get candidate_id
        interview = session.exec(select(InterviewSession).where(InterviewSession.access_token == interview_token)).first()
        if not interview:
            raise HTTPException(status_code=401, detail="Invalid interview token")
        if target_user_id is not None and target_user_id != interview.candidate_id:
            raise HTTPException(status_code=403, detail="Token mismatch for user_id")
        target_user_id = interview.candidate_id
        # Token access granted!
    elif current_user:
        if target_user_id is None:
            target_user_id = current_user.id
            
        # Permission check for logged-in user
        if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.id != target_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this resume")
    else:
        raise HTTPException(status_code=401, detail="Authentication required (Token or Login)")
    
    user = session.get(User, target_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")

    # If it's a Cloudinary URL, return metadata instead of the file
    if user.resume_path.startswith('https://'):
        return ApiResponse(
            status_code=200,
            data=ResumeResponse(
                user_id=target_user_id,
                resume_url=user.resume_path
            ),
            message="Resume details retrieved successfully"
        )
    
    # Return the actual file for local storage
    if not os.path.exists(user.resume_path):
        raise HTTPException(status_code=404, detail="Resume file not found")
    
    return FileResponse(
        path=user.resume_path,
        filename=f"resume_{target_user_id}.pdf",
        media_type="application/pdf"
    )

@router.get("/generate-prompt/{user_id}", response_model=ApiResponse[dict])
async def generate_resume_prompt(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Extract text from a user's resume and generate a prompt for question generation.
    Admins can generate for any user, users only for themselves.
    """
    # Permission check
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this resume")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.resume_path:
        raise HTTPException(status_code=404, detail="Resume not found for this user")

    temp_file_path = None
    try:
        # 1. Handle Cloudinary or Local Path
        if user.resume_path.startswith('https://') or user.resume_path.startswith('http://'):
            # Download from URL
            response = requests.get(user.resume_path, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to download resume from source")
            
            # Create a temporary file with the correct extension
            ext = os.path.splitext(user.resume_path.split('?')[0])[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(response.content)
                temp_file_path = tmp.name
        else:
            # Local path
            if not os.path.exists(user.resume_path):
                raise HTTPException(status_code=404, detail="Resume file not found on server")
            temp_file_path = user.resume_path

        # 2. Extract and AI-Structure the Resume
        nlp_service = get_nlp_service()
        resume_text = nlp_service.extract_text_from_file(temp_file_path)
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from the resume")

        # Use AI to clean and arrange the resume data for a better prompt
        structured_resume = nlp_service.arrange_resume_with_ai(resume_text)

        # 3. Format Structured Prompt
        # The prompt is designed to guide the AI in generating a high-quality question paper.
        prompt = (
            f"Objective: Generate a comprehensive interview question paper based on the candidate's background summarized below.\n\n"
            f"Instructions:\n"
            f"1. Technical Depth: Align the question difficulty with the candidate's years of experience and mentioned seniority level.\n"
            f"2. Question Mix: Include a balanced mix of core conceptual questions, practical implementation problems, and at least 2 situational/scenario-based questions.\n"
            f"3. Focus Areas: Identify the primary technical stack (languages, frameworks, tools) from the summary and focus 70% of the questions on those areas.\n"
            f"4. Professionalism: Ensure questions are industry-standard and clear.\n\n"
            f"Candidate Profile Summary:\n"
            f"{structured_resume}"
        )

        return ApiResponse(
            status_code=200,
            data={"ai_prompt": prompt},
            message="Resume prompt generated successfully"
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")
    finally:
        # Clean up temp file ONLY if it was a downloaded one
        if temp_file_path and user.resume_path.startswith('http') and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

# @router.post("/upload", response_model=ApiResponse[dict])
# async def upload_resume(
#     file: UploadFile = File(...),
#     user_id: Optional[int] = Form(None),
#     current_user: User = Depends(get_current_user),
#     session: Session = Depends(get_session)
# ):
#     """
#     Upload a resume file for a user.
#     Admins can upload for any user, users can only upload for themselves.
#     """
#     # Permission check
#     target_user_id = user_id if user_id else current_user.id
#     if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and current_user.id != target_user_id:
#         raise HTTPException(status_code=403, detail="Not authorized to upload resume for this user")
#     
#     # Validate file type
#     if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
#         raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX allowed.")
#     
#     # Get target user
#     target_user = session.get(User, target_user_id)
#     if not target_user:
#         raise HTTPException(status_code=404, detail="Target user not found")
#     
#     # Upload to Cloudinary
#     try:
#         from ..services.cloudinary_service import CloudinaryService
#         cloudinary_service = CloudinaryService()
#         
#         await file.seek(0)
#         resume_url = cloudinary_service.upload_resume(file.file, folder="resumes")
#         
#         if resume_url:
#             target_user.resume_path = resume_url
#             session.add(target_user)
#             session.commit()
#             
#             return Response(
#                 content=ApiResponse(
#                     status_code=201,
#                     data={"resume_url": resume_url, "user_id": target_user_id},
#                     message="Resume uploaded successfully"
#                 ).model_dump_json(),
#                 status_code=201,
#                 media_type="application/json"
#             )
#         else:
#             raise HTTPException(status_code=500, detail="Failed to upload resume to Cloudinary")
#             
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Resume upload failed: {str(e)}")
# 
# @router.post("/upload/{user_id}", response_model=ApiResponse[dict])
# async def upload_resume_for_user(
#     user_id: int,
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     session: Session = Depends(get_session)
# ):
#     """Upload a resume file for a specific user (admin only)."""
#     # Permission check - only admins can upload for other users
#     if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
#         raise HTTPException(status_code=403, detail="Not authorized to upload resume for other users")
#     
#     # Validate file type
#     if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
#         raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOC, DOCX allowed.")
#     
#     # Get target user
#     target_user = session.get(User, user_id)
#     if not target_user:
#         raise HTTPException(status_code=404, detail="Target user not found")
#     
#     # Upload to Cloudinary
#     try:
#         from ..services.cloudinary_service import CloudinaryService
#         cloudinary_service = CloudinaryService()
#         
#         await file.seek(0)
#         resume_url = cloudinary_service.upload_resume(file.file, folder="resumes")
#         
#         if resume_url:
#             target_user.resume_path = resume_url
#             session.add(target_user)
#             session.commit()
#             
#             return Response(
#                 content=ApiResponse(
#                     status_code=201,
#                     data={"resume_url": resume_url, "user_id": user_id},
#                     message="Resume uploaded successfully"
#                 ).model_dump_json(),
#                 status_code=201,
#                 media_type="application/json"
#             )
#         else:
#             raise HTTPException(status_code=500, detail="Failed to upload resume to Cloudinary")
#             
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Resume upload failed: {str(e)}")