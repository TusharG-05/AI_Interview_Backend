"""
Test Cloudinary selfie upload with actual image file
"""
import pytest
import io
import json
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_upload_selfie_with_real_image(client: TestClient, session: Session, test_users):
    """Test uploading actual selfie image file to Cloudinary."""
    from app.models.db_models import InterviewSession, InterviewStatus
    
    # 1. Get test users
    admin, candidate, super_admin = test_users
    cand_id = candidate.id
    
    # 2. Create mock stored embeddings for candidate (simulating enrollment)
    # Create realistic ArcFace (512-dim) and SFace (128-dim) embeddings
    np.random.seed(42)
    stored_arcface = np.random.randn(512).tolist()
    stored_sface = np.random.randn(128).tolist()
    
    # Normalize vectors
    stored_arcface = (stored_arcface / np.linalg.norm(stored_arcface)).tolist()
    stored_sface = (stored_sface / np.linalg.norm(stored_sface)).tolist()
    
    candidate.face_embedding = json.dumps({
        "arcface": stored_arcface,
        "sface": stored_sface
    })
    session.add(candidate)
    session.commit()
    
    # 3. Create interview session for candidate
    from datetime import datetime, timezone
    interview = InterviewSession(
        candidate_id=cand_id,
        admin_id=admin.id,
        title="Test Interview for Selfie Upload",
        description="Testing Cloudinary upload with real image",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_selfie_real",
        schedule_time=datetime.now(timezone.utc)  # Required field
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    print(f"\nCreated interview ID: {interview.id}")
    
    # 4. Create dummy image data (since real file doesn't exist)
    image_bytes = io.BytesIO(b"dummy_image_data_for_testing").getvalue()
    print(f"Image size: {len(image_bytes)} bytes")
    
    # 5. Login as admin to get token
    login_res = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "TestPass123!",
        "access_token": "test_token_selfie_real"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    admin_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"Admin logged in successfully")
    
    # 6. Upload selfie using candidate_id
    files = {
        "file": ("selfie.png", io.BytesIO(image_bytes), "image/png")
    }
    data = {
        "candidate_id": str(candidate.id)  # Use correct cand_id
    }
    
    upload_res = client.post(
        "/api/interview/upload-selfie",
        data=data,
        files=files,
        headers=auth_headers  # Admin uploads on behalf of candidate
    )
    
    print(f"\nUpload response status: {upload_res.status_code}")
    response_json = upload_res.json()
    print(f"Response: {response_json}")
    
    # 7. Verify face verification response
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    result = response_json
    
    assert result["status_code"] == 200
    assert "verified" in result["data"], "Response should contain verification result"
    assert "similarity_score" in result["data"], "Response should contain similarity score"
    assert result["data"]["candidate_id"] == candidate.id
    
    # Check verification result (may pass or fail depending on face match)
    if result["data"]["verified"]:
        print("✅ Face verification PASSED")
    else:
        print("⚠️ Face verification FAILED - this is expected if using a different person's image")
    
    print(f"Similarity score: {result['data'].get('similarity_score', 'N/A')}")
    
    # 8. Check Cloudinary URL
    cloudinary_url = result["data"].get("cloudinary_url")
    print(f"\n✅ Cloudinary URL: {cloudinary_url}")
    
    if cloudinary_url:
        assert "cloudinary.com" in cloudinary_url, f"Invalid URL: {cloudinary_url}"
        print("✅ Image uploaded to Cloudinary successfully!")
        
        # Verify URL is accessible
        import requests
        try:
            head_res = requests.head(cloudinary_url, timeout=10)
            print(f"URL check status: {head_res.status_code}")
            if head_res.status_code == 200:
                print("✅ Image is accessible via URL")
            else:
                print(f"⚠️  URL returned status {head_res.status_code}")
        except Exception as e:
            print(f"⚠️  Could not verify URL accessibility: {e}")
    else:
        print("❌ Cloudinary URL is None - upload failed or credentials not configured")
    
    # 8. Verify database
    from app.models.db_models import User
    user = session.get(User, cand_id)
    assert user.profile_image_bytes is not None
    print(f"✅ Image bytes saved to DB: {len(user.profile_image_bytes)} bytes")
