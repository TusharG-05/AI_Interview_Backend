"""
Test face verification in interview selfie upload endpoint
"""
import pytest
import io
import numpy as np
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock


def test_face_verification_success(client: TestClient, session: Session, test_users):
    """Test successful face verification when selfie matches stored embeddings."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    import tempfile
    import os
    
    # 1. Get test users
    admin, candidate, super_admin = test_users
    cand_id = candidate.id
    
    # 2. Create mock stored embeddings for candidate (simulating enrollment)
    # Create realistic ArcFace (512-dim) and SFace (128-dim) embeddings
    np.random.seed(42)
    stored_arcface = np.random.randn(512).tolist()
    stored_sface = np.random.randn(128).tolist()
    
    # Normalize the vectors
    stored_arcface = (stored_arcface / np.linalg.norm(stored_arcface)).tolist()
    stored_sface = (stored_sface / np.linalg.norm(stored_sface)).tolist()
    
    candidate.face_embedding = json.dumps({
        "arcface": stored_arcface,
        "sface": stored_sface
    })
    session.add(candidate)
    session.commit()
    
    # 3. Create interview session
    interview = InterviewSession(
        candidate_id=cand_id,
        admin_id=admin.id,
        title="Test Interview for Face Verification",
        description="Testing face verification",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_face_verify",
        schedule_time=datetime.now(timezone.utc)
    )
    session.add(interview)
    session.commit()
    
    # 4. Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!",
        "access_token": "test_token_face_verify"
    })
    assert login_res.status_code == 200
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 5. Mock DeepFace to return embeddings that will produce high similarity
    with patch('deepface.DeepFace.represent') as mock_represent:
        # Return embeddings that are very similar to stored (cosine sim > 0.40)
        mock_represent.side_effect = [
            [{"embedding": stored_arcface}],  # ArcFace - same as stored
            [{"embedding": stored_sface}]     # SFace - same as stored
        ]
        
        # Create a dummy image file
        files = {
            "file": ("selfie.png", io.BytesIO(b"fake_image_data_for_testing"), "image/png")
        }
        data = {"candidate_id": str(cand_id)}
        
        upload_res = client.post(
            "/api/interview/upload-selfie",
            data=data,
            files=files,
            headers=auth_headers
        )
        
        print(f"\nFace verification response: {upload_res.json()}")
        
        # 6. Verify successful verification
        assert upload_res.status_code == 200
        result = upload_res.json()
        
        assert result["status_code"] == 200
        assert result["data"]["verified"] is True
        assert result["data"]["candidate_id"] == cand_id
        assert "similarity_score" in result["data"]
        assert result["data"]["similarity_score"] > 0.40
        assert result["data"]["threshold"] == 0.40
        assert "Face verified successfully" in result["message"]


def test_face_verification_failure_mismatch(client: TestClient, session: Session, test_users):
    """Test face verification failure when selfie doesn't match stored embeddings."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    # 1. Get test users
    admin, candidate, super_admin = test_users
    cand_id = candidate.id
    
    # 2. Create stored embeddings for candidate
    np.random.seed(42)
    stored_arcface = np.random.randn(512).tolist()
    stored_sface = np.random.randn(128).tolist()
    stored_arcface = (stored_arcface / np.linalg.norm(stored_arcface)).tolist()
    stored_sface = (stored_sface / np.linalg.norm(stored_sface)).tolist()
    
    candidate.face_embedding = json.dumps({
        "arcface": stored_arcface,
        "sface": stored_sface
    })
    session.add(candidate)
    session.commit()
    
    # 3. Create interview session
    interview = InterviewSession(
        candidate_id=cand_id,
        admin_id=admin.id,
        title="Test Interview Face Mismatch",
        description="Testing face verification failure",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_mismatch",
        schedule_time=datetime.now(timezone.utc)
    )
    session.add(interview)
    session.commit()
    
    # 4. Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!",
        "access_token": "test_token_mismatch"
    })
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 5. Mock DeepFace to return completely different embeddings (low similarity)
    with patch('deepface.DeepFace.represent') as mock_represent:
        # Return completely different embeddings (orthogonal vectors)
        different_arcface = np.random.randn(512).tolist()
        different_sface = np.random.randn(128).tolist()
        # Make them orthogonal to stored by subtracting projection
        proj_arc = np.dot(different_arcface, stored_arcface) * np.array(stored_arcface)
        different_arcface = (np.array(different_arcface) - proj_arc).tolist()
        proj_sface = np.dot(different_sface, stored_sface) * np.array(stored_sface)
        different_sface = (np.array(different_sface) - proj_sface).tolist()
        
        mock_represent.side_effect = [
            [{"embedding": different_arcface}],
            [{"embedding": different_sface}]
        ]
        
        files = {
            "file": ("selfie.png", io.BytesIO(b"different_person_image"), "image/png")
        }
        data = {"candidate_id": str(cand_id)}
        
        upload_res = client.post(
            "/api/interview/upload-selfie",
            data=data,
            files=files,
            headers=auth_headers
        )
        
        print(f"\nFace mismatch response: {upload_res.json()}")
        
        # 6. Verify failed verification (but HTTP 200 with verified=false)
        assert upload_res.status_code == 200
        result = upload_res.json()
        
        assert result["data"]["verified"] is False
        assert result["data"]["similarity_score"] < 0.40
        assert "Face verification failed" in result["message"]


def test_face_verification_no_stored_embeddings(client: TestClient, session: Session, test_users):
    """Test error when candidate has no stored embeddings (not enrolled)."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    # 1. Get test users - use a fresh candidate without embeddings
    admin, candidate, super_admin = test_users
    cand_id = candidate.id
    
    # Ensure no face_embedding
    candidate.face_embedding = None
    session.add(candidate)
    session.commit()
    
    # 2. Create interview session
    interview = InterviewSession(
        candidate_id=cand_id,
        admin_id=admin.id,
        title="Test No Embeddings",
        description="Testing missing embeddings error",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_no_embed",
        schedule_time=datetime.now(timezone.utc)
    )
    session.add(interview)
    session.commit()
    
    # 3. Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!",
        "access_token": "test_token_no_embed"
    })
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 4. Upload without stored embeddings
    files = {
        "file": ("selfie.png", io.BytesIO(b"any_image_data"), "image/png")
    }
    data = {"candidate_id": str(cand_id)}
    
    upload_res = client.post(
        "/api/interview/upload-selfie",
        data=data,
        files=files,
        headers=auth_headers
    )
    
    print(f"\nNo embeddings response: {upload_res.json()}")
    
    # 5. Verify error response
    assert upload_res.status_code == 400
    result = upload_res.json()
    assert "No enrollment selfie found" in result["message"]


def test_face_verification_no_face_detected(client: TestClient, session: Session, test_users):
    """Test error when no face is detected in uploaded image."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    # 1. Get test users
    admin, candidate, super_admin = test_users
    cand_id = candidate.id
    
    # 2. Create stored embeddings
    np.random.seed(42)
    stored_arcface = np.random.randn(512).tolist()
    stored_sface = np.random.randn(128).tolist()
    stored_arcface = (stored_arcface / np.linalg.norm(stored_arcface)).tolist()
    stored_sface = (stored_sface / np.linalg.norm(stored_sface)).tolist()
    
    candidate.face_embedding = json.dumps({
        "arcface": stored_arcface,
        "sface": stored_sface
    })
    session.add(candidate)
    session.commit()
    
    # 3. Create interview session
    interview = InterviewSession(
        candidate_id=cand_id,
        admin_id=admin.id,
        title="Test No Face",
        description="Testing no face detection error",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_no_face",
        schedule_time=datetime.now(timezone.utc)
    )
    session.add(interview)
    session.commit()
    
    # 4. Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!",
        "access_token": "test_token_no_face"
    })
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 5. Mock DeepFace to fail face detection
    with patch('deepface.DeepFace.represent') as mock_represent:
        # Both models fail to detect face
        mock_represent.side_effect = [
            Exception("Face could not be detected"),
            Exception("Face could not be detected")
        ]
        
        files = {
            "file": ("selfie.png", io.BytesIO(b"no_face_image"), "image/png")
        }
        data = {"candidate_id": str(cand_id)}
        
        upload_res = client.post(
            "/api/interview/upload-selfie",
            data=data,
            files=files,
            headers=auth_headers
        )
        
        print(f"\nNo face response: {upload_res.json()}")
        
        # 6. Verify error
        assert upload_res.status_code == 400
        result = upload_res.json()
        assert "Failed to generate face embeddings" in result["message"]


def test_face_verification_candidate_not_found(client: TestClient, session: Session, test_users):
    """Test error when candidate_id doesn't exist."""
    from app.models.db_models import InterviewSession, InterviewStatus
    from datetime import datetime, timezone
    
    # 1. Get test users
    admin, candidate, super_admin = test_users
    
    # 2. Create interview session
    interview = InterviewSession(
        candidate_id=candidate.id,
        admin_id=admin.id,
        title="Test Invalid Candidate",
        description="Testing invalid candidate error",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_invalid",
        schedule_time=datetime.now(timezone.utc)
    )
    session.add(interview)
    session.commit()
    
    # 3. Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!",
        "access_token": "test_token_invalid"
    })
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 4. Upload with non-existent candidate_id
    files = {
        "file": ("selfie.png", io.BytesIO(b"image_data"), "image/png")
    }
    data = {"candidate_id": "99999"}  # Non-existent ID
    
    upload_res = client.post(
        "/api/interview/upload-selfie",
        data=data,
        files=files,
        headers=auth_headers
    )
    
    print(f"\nInvalid candidate response: {upload_res.json()}")
    
    # 5. Verify error
    assert upload_res.status_code == 404
    result = upload_res.json()
    assert "Candidate not found" in result["message"]
