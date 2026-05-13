import pytest
import io
import json
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

def test_upload_selfie_to_cloudinary(client: TestClient, session: Session, test_users):
    """Test that selfie is uploaded to Cloudinary after verification."""
    from app.models.db_models import InterviewSession, InterviewStatus, User
    from datetime import datetime, timezone
    
    admin, candidate, _ = test_users
    
    # Seed candidate with valid JSON face embeddings
    stored_arcface = [0.1]*512
    stored_sface = [0.1]*128
    candidate.face_embedding = json.dumps({
        "ArcFace": stored_arcface,
        "SFace": stored_sface
    })
    session.add(candidate)
    session.commit()
    session.refresh(candidate)

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
        
        mock_upload.return_value = "https://cloudinary.com/test_selfie.jpg"
        
        # Login to get token
        login_res = client.post("/api/auth/login", json={
            "email": admin.email,
            "password": "TestPass123!",
            "access_token": "any"
        })
        token = login_res.json()["data"]["access_token"]
        
        files = {"file": ("selfie.jpg", io.BytesIO(b"fake-image-data"), "image/jpeg")}
        response = client.post(
            "/api/interview/upload-selfie",
            data={"candidate_id": str(candidate.id)},
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "cloudinary_url" in data
        assert data["cloudinary_url"] == "https://cloudinary.com/test_selfie.jpg"
        mock_upload.assert_called_once()
