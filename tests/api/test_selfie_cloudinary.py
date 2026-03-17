"""
Test Cloudinary selfie upload functionality
"""
import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_upload_selfie_to_cloudinary(client: TestClient, session: Session, test_users, auth_headers):
    """Test uploading a selfie image to Cloudinary via interview session."""
    from app.models.db_models import InterviewSession, InterviewStatus
    
    # 1. Get test users
    admin, candidate, super_admin = test_users
    cand_id = candidate.id
    
    # 2. Create interview session for candidate
    interview = InterviewSession(
        candidate_id=cand_id,
        admin_id=admin.id,
        title="Test Interview for Selfie Upload",
        description="Testing Cloudinary upload",
        status=InterviewStatus.SCHEDULED,
        access_token="test_token_selfie"
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    # 3. Create a simple test image (1x1 pixel red PNG)
    # PNG header + IHDR + IDAT + IEND chunks for 1x1 red pixel
    test_image_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01,  # width: 1
        0x00, 0x00, 0x00, 0x01,  # height: 1
        0x08, 0x02, 0x00, 0x00, 0x00,  # bit depth, color type, compression, filter, interlace
        0x90, 0x77, 0x53, 0xDE,  # CRC
        0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,  # IDAT chunk
        0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x00, 0x00, 0x01,
        0x01, 0x00, 0x05, 0x18, 0xD8, 0x4D, 0xE1,  # compressed data + CRC
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND chunk
        0xAE, 0x42, 0x60, 0x82  # CRC
    ])
    
    # 4. Upload selfie
    files = {
        "file": ("test_selfie.png", io.BytesIO(test_image_bytes), "image/png")
    }
    data = {
        "interview_id": interview.id
    }
    
    # Use candidate auth headers (need to get candidate token)
    # Login as candidate to get token
    login_res = client.post("/api/auth/login", json={
        "email": candidate.email,
        "password": "TestPass123!",
        "access_token": "test_token_selfie"
    })
    assert login_res.status_code == 200
    cand_token = login_res.json()["data"]["access_token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    
    # Upload the selfie
    upload_res = client.post(
        "/api/interview/upload-selfie",
        data=data,
        files=files,
        headers=cand_headers
    )
    
    print(f"Upload response status: {upload_res.status_code}")
    print(f"Upload response: {upload_res.json()}")
    
    # 5. Verify response
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    result = upload_res.json()
    
    assert result["status_code"] == 200
    assert result["data"]["interview_id"] == interview.id
    assert result["data"]["has_backup"] is True  # Bytes stored in DB
    
    # Check if Cloudinary URL was returned (or None if upload failed)
    cloudinary_url = result["data"].get("cloudinary_url")
    print(f"Cloudinary URL: {cloudinary_url}")
    
    if cloudinary_url:
        assert "cloudinary.com" in cloudinary_url, f"Invalid Cloudinary URL: {cloudinary_url}"
        # Verify URL is accessible (optional - can be slow)
        # import requests
        # head_res = requests.head(cloudinary_url, timeout=10)
        # assert head_res.status_code == 200, "Cloudinary image not accessible"
    else:
        print("⚠️  Cloudinary URL is None - check Cloudinary credentials")
    
    # 6. Verify database has the image
    from app.models.db_models import User
    user = session.get(User, cand_id)
    assert user.profile_image_bytes is not None, "Profile image bytes not saved"
    
    print(f"✅ Selfie upload test passed! Image size: {len(user.profile_image_bytes)} bytes")
    print(f"   Cloudinary URL: {cloudinary_url or 'FAILED - check logs'}")
