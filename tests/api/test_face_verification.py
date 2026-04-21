"""
Test face verification in interview selfie upload endpoint
"""
import pytest
import io
import numpy as np
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch


def test_face_verification_success(client: TestClient, session: Session, test_users):
    """Test successful face verification when selfie matches stored embeddings."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    admin, candidate, _ = test_users
    cand_id = candidate.id
    
    np.random.seed(42)
    stored_arcface = np.random.randn(512).tolist()
    stored_sface = np.random.randn(128).tolist()
    stored_arcface = (stored_arcface / np.linalg.norm(stored_arcface)).tolist()
    stored_sface = (stored_sface / np.linalg.norm(stored_sface)).tolist()
    
    candidate.face_embedding = json.dumps({"ArcFace": stored_arcface, "SFace": stored_sface})
    session.add(candidate)
    session.commit()
    
    interview = InterviewSession(candidate_id=cand_id, admin_id=admin.id, title="Test Success", status=InterviewStatus.SCHEDULED, access_token="test_token_success", schedule_time=datetime.now(timezone.utc))
    session.add(interview)
    session.commit()
    
    login_res = client.post("/api/auth/login", json={"email": admin.email, "password": "TestPass123!", "access_token": "test_token_success"})
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    def mock_rep(*args, **kwargs):
        m = kwargs.get("model_name")
        if m == "ArcFace": return [{"embedding": stored_arcface}]
        return [{"embedding": stored_sface}]

    mock_modal_res = {"success": True, "embedding": stored_arcface}
    mock_modal_cls = MagicMock()
    mock_modal_cls().get_embedding.remote.return_value = mock_modal_res

    with patch("app.core.config.USE_MODAL", False), \
         patch("app.services.face.get_modal_embedding", return_value=mock_modal_cls), \
         patch("deepface.DeepFace.represent", side_effect=mock_rep):
        
        files = {"file": ("selfie.png", io.BytesIO(b"data"), "image/png")}
        res = client.post("/api/interview/upload-selfie", data={"candidate_id": str(cand_id)}, files=files, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["data"]["verified"] is True


def test_face_verification_failure_mismatch(client: TestClient, session: Session, test_users):
    """Test face verification failure when selfie doesn't match."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    admin, candidate, _ = test_users
    cand_id = candidate.id
    
    np.random.seed(42)
    stored_arcface = np.random.randn(512).tolist()
    stored_sface = np.random.randn(128).tolist()
    stored_arcface = (stored_arcface / np.linalg.norm(stored_arcface)).tolist()
    stored_sface = (stored_sface / np.linalg.norm(stored_sface)).tolist()
    
    candidate.face_embedding = json.dumps({"ArcFace": stored_arcface, "SFace": stored_sface})
    session.add(candidate)
    session.commit()
    
    interview = InterviewSession(candidate_id=cand_id, admin_id=admin.id, title="Test Fail", status=InterviewStatus.SCHEDULED, access_token="test_token_fail", schedule_time=datetime.now(timezone.utc))
    session.add(interview)
    session.commit()
    
    login_res = client.post("/api/auth/login", json={"email": admin.email, "password": "TestPass123!", "access_token": "test_token_fail"})
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    diff_arcface = [0.0] * 512
    diff_arcface[0] = 1.0
    diff_sface = [0.0] * 128
    diff_sface[0] = 1.0
    
    def mock_rep(*args, **kwargs):
        m = kwargs.get("model_name")
        if m == "ArcFace": return [{"embedding": diff_arcface}]
        return [{"embedding": diff_sface}]

    mock_modal_res = {"success": True, "embedding": diff_arcface}
    mock_modal_cls = MagicMock()
    mock_modal_cls().get_embedding.remote.return_value = mock_modal_res

    with patch("app.core.config.USE_MODAL", False), \
         patch("app.services.face.get_modal_embedding", return_value=mock_modal_cls), \
         patch("deepface.DeepFace.represent", side_effect=mock_rep):
        
        files = {"file": ("selfie.png", io.BytesIO(b"data"), "image/png")}
        res = client.post("/api/interview/upload-selfie", data={"candidate_id": str(cand_id)}, files=files, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["data"]["verified"] is False


def test_face_verification_no_stored_embeddings(client: TestClient, session: Session, test_users):
    """Test auto-enrollment path."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    admin, candidate, _ = test_users
    candidate.face_embedding = None
    session.add(candidate)
    session.commit()
    
    interview = InterviewSession(candidate_id=candidate.id, admin_id=admin.id, title="Test Enroll", status=InterviewStatus.SCHEDULED, access_token="test_token_enroll", schedule_time=datetime.now(timezone.utc))
    session.add(interview)
    session.commit()
    
    login_res = client.post("/api/auth/login", json={"email": admin.email, "password": "TestPass123!", "access_token": "test_token_enroll"})
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    def mock_rep(*args, **kwargs):
        m = kwargs.get("model_name")
        if m == "ArcFace": return [{"embedding": [0.5] * 512}]
        return [{"embedding": [0.5] * 128}]

    mock_modal_res = {"success": True, "embedding": [0.5] * 512}
    mock_modal_cls = MagicMock()
    mock_modal_cls().get_embedding.remote.return_value = mock_modal_res

    with patch("app.core.config.USE_MODAL", False), \
         patch("app.services.face.get_modal_embedding", return_value=mock_modal_cls), \
         patch("deepface.DeepFace.represent", side_effect=mock_rep):
        
        files = {"file": ("selfie.png", io.BytesIO(b"data"), "image/png")}
        res = client.post("/api/interview/upload-selfie", data={"candidate_id": str(candidate.id)}, files=files, headers=auth_headers)
        assert res.status_code == 200
        assert "Face enrolled" in res.json()["message"]


def test_face_verification_no_face_detected(client: TestClient, session: Session, test_users):
    """Test fallback when face is not detected."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    admin, candidate, _ = test_users
    candidate.face_embedding = json.dumps({"ArcFace": [0.1]*512, "SFace": [0.1]*128})
    session.add(candidate)
    session.commit()
    
    interview = InterviewSession(candidate_id=candidate.id, admin_id=admin.id, title="Test No Face", status=InterviewStatus.SCHEDULED, access_token="test_token_noface", schedule_time=datetime.now(timezone.utc))
    session.add(interview)
    session.commit()
    
    login_res = client.post("/api/auth/login", json={"email": admin.email, "password": "TestPass123!", "access_token": "test_token_noface"})
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    mock_modal_res = {"success": False, "error": "Face could not be detected"}
    mock_modal_cls = MagicMock()
    mock_modal_cls().get_embedding.remote.return_value = mock_modal_res

    with patch("app.core.config.USE_MODAL", False), \
         patch("app.services.face.get_modal_embedding", return_value=mock_modal_cls), \
         patch("deepface.DeepFace.represent", side_effect=Exception("Face could not be detected")):
        
        files = {"file": ("selfie.png", io.BytesIO(b"data"), "image/png")}
        res = client.post("/api/interview/upload-selfie", data={"candidate_id": str(candidate.id)}, files=files, headers=auth_headers)
        assert res.status_code == 400
        assert "Failed to generate face embeddings" in res.json()["message"]


def test_face_verification_candidate_not_found(client: TestClient, session: Session, test_users):
    """Test error when candidate_id is invalid."""
    admin, _, _ = test_users
    
    login_res = client.post("/api/auth/login", json={"email": admin.email, "password": "TestPass123!", "access_token": "any_token"})
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    
    files = {"file": ("selfie.png", io.BytesIO(b"data"), "image/png")}
    res = client.post("/api/interview/upload-selfie", data={"candidate_id": "99999"}, files=files, headers=auth_headers)
    # The error message from ApiResponse might vary, but status code should be 404
    assert res.status_code == 404
    assert "Candidate not found" in res.json()["message"]
