import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.db_models import User, InterviewSession, InterviewStatus
import io
import uuid

from unittest.mock import patch, MagicMock

def test_refactored_selfie_uploads(client: TestClient, session: Session, test_users, auth_headers):
    from app.auth.security import create_access_token
    admin, candidate, super_admin = test_users
    c_headers = {"Authorization": f"Bearer {create_access_token(data={'sub': candidate.email})}"}
    
    # Prerequisite: Create an interview session for the candidate
    from app.models.db_models import QuestionPaper, Team
    paper = QuestionPaper(name="Selfie Test Paper", admin_user=admin.id)
    team = Team(name="Selfie Team")
    session.add(paper)
    session.add(team)
    session.commit()
    
    from datetime import datetime, timezone, timedelta
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        team_id=team.id,
        access_token="selfie-test-token",
        status=InterviewStatus.SCHEDULED,
        schedule_time=datetime.now(timezone.utc),
        duration_minutes=60
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    # 1. Test Candidate Upload (Should generate EMBEDDINGS and set STATUS)
    image_content = b"fake-image-binary-content"
    # Mock Modal and DeepFace
    with patch("app.services.face.USE_MODAL", True), \
         patch("app.services.face.get_modal_embedding") as mock_get_modal, \
         patch("deepface.DeepFace.represent") as mock_rep:
        
        # Mock Modal embedding call
        mock_modal_instance = MagicMock()
        mock_modal_instance.get_embedding.remote.return_value = {"success": True, "embedding": [0.5, 0.6, 0.7]}
        mock_get_modal.return_value = MagicMock(return_value=mock_modal_instance)
        
        # Mocking the return of DeepFace.represent for SFace
        mock_rep.return_value = [{"embedding": [0.1, 0.2, 0.3]}]
        
        response = client.post(
            f"/api/candidate/upload-selfie?interview_id={interview.id}",
            headers=c_headers,
            files={"file": ("selfie.jpg", io.BytesIO(image_content), "image/jpeg")}
        )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["has_embeddings"] is True
    assert data["status_updated"] is True
    
    # Verify DB
    session.expire_all() # Ensure we fetch fresh data
    db_candidate = session.get(User, candidate.id)
    import json
    embeddings = json.loads(db_candidate.face_embedding)
    assert "ArcFace" in embeddings
    assert "SFace" in embeddings
    assert embeddings["ArcFace"] == [0.5, 0.6, 0.7] # From Modal mock
    
    # Verify Status Change (triggered by Candidate API)
    db_interview = session.get(InterviewSession, interview.id)
    from app.models.db_models import CandidateStatus
    assert db_interview.current_status == CandidateStatus.SELFIE_UPLOADED.value

    # 2. Test Interview Upload (Should handle VERIFICATION and CLOUDINARY)
    # Reset profile_image to ensure we see the update
    db_candidate.profile_image = None
    session.add(db_candidate)
    session.commit()
    
    # Mock Cloudinary, Modal and DeepFace for verification context
    with patch("app.services.cloudinary_service.CloudinaryService.upload_image") as mock_cloud, \
         patch("app.services.face.USE_MODAL", True), \
         patch("app.services.face.get_modal_embedding") as mock_get_modal_verify, \
         patch("deepface.DeepFace.represent") as mock_rep_verify:
        
        mock_cloud.return_value = "https://cloudinary.com/verification-selfie.jpg"
        
        # Mock Modal embedding call (Perfect Match)
        mock_modal_instance_verify = MagicMock()
        mock_modal_instance_verify.get_embedding.remote.return_value = {"success": True, "embedding": [0.5, 0.6, 0.7]}
        mock_get_modal_verify.return_value = MagicMock(return_value=mock_modal_instance_verify)
        
        # Mocking representation for SFace
        mock_rep_verify.return_value = [{"embedding": [0.1, 0.2, 0.3]}]
        
        response = client.post(
            "/api/interview/upload-selfie",
            headers=c_headers,
            data={"candidate_id": candidate.id},
            files={"file": ("interview_selfie.jpg", io.BytesIO(image_content), "image/jpeg")}
        )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["verified"] is True
    assert data["arcface_score"] > 0.99 # Should be 1.0 due to perfect match mock
    assert data["sface_score"] > 0.99
    
    print("Modal/ArcFace fallback verification successful!")
