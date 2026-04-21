import pytest
import io
import json
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

def test_upload_selfie_with_real_image(client: TestClient, session: Session, test_users):
    """Test selfie upload with a real image (mocked DeepFace)."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    admin, candidate, _ = test_users
    cand_id = candidate.id
    
    # Seed candidate with valid JSON face embeddings
    stored_arcface = [0.1]*512
    stored_sface = [0.1]*128
    candidate.face_embedding = json.dumps({
        "ArcFace": stored_arcface,
        "SFace": stored_sface
    })
    session.add(candidate)
    session.commit()
    
    interview = InterviewSession(
        candidate_id=cand_id, 
        admin_id=admin.id, 
        title="Real Image Test", 
        status=InterviewStatus.SCHEDULED, 
        access_token="real_token", 
        schedule_time=datetime.now(timezone.utc)
    )
    session.add(interview)
    session.commit()
    
    # Login as admin
    login_res = client.post("/api/auth/login", json={
        "email": admin.email, 
        "password": "TestPass123!", 
        "access_token": "real_token"
    })
    token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    mock_modal_res = {"success": True, "embedding": stored_arcface}
    mock_modal_cls = MagicMock()
    mock_modal_cls().get_embedding.remote.return_value = mock_modal_res

    def mock_represent_side_effect(*args, **kwargs):
        model_name = kwargs.get("model_name", "ArcFace")
        if model_name == "ArcFace":
            return [{"embedding": [0.1]*512}]
        else:
            return [{"embedding": [0.1]*128}]

    with patch("app.core.config.USE_MODAL", False), \
         patch("app.services.face.get_modal_embedding", return_value=mock_modal_cls), \
         patch("deepface.DeepFace.represent", side_effect=mock_represent_side_effect), \
         patch("app.services.cloudinary_service.CloudinaryService.upload_image") as mock_upload:
        
        mock_upload.return_value = "https://cloudinary.com/real_selfie.jpg"
        
        files = {"file": ("real_selfie.jpg", io.BytesIO(b"real-image-data"), "image/jpeg")}
        res = client.post(
            "/api/interview/upload-selfie", 
            data={"candidate_id": str(cand_id)}, 
            files=files, 
            headers=auth_headers
        )
        
        assert res.status_code == 200
        assert res.json()["data"]["verified"] is True
        assert "cloudinary_url" in res.json()["data"]
