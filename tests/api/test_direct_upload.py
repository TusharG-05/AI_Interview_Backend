
import pytest
import io
import uuid
from unittest.mock import patch, MagicMock

def test_direct_upload_workflow(client, session, test_users, auth_headers):
    """Test creating and updating users with direct resume uploads."""
    admin, candidate, super_admin = test_users
    
    # Mock Cloudinary for this test
    with patch("app.routers.admin.get_cloudinary_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.upload_resume.return_value = "https://mock-cloudinary.com/resume.pdf"
        mock_get_service.return_value = mock_service
        
        # 1. CREATE USER with Resume
        cand_email = f"direct_{uuid.uuid4().hex[:6]}@test.com"
        resume_content = b"%PDF-1.4\nInitial Resume Content"
        
        create_res = client.post(
            "/api/admin/users",
            headers=auth_headers,
            data={
                "email": cand_email,
                "full_name": "Direct Candidate",
                "password": "password123",
                "role": "CANDIDATE"
            },
            files={"resume": ("initial.pdf", io.BytesIO(resume_content), "application/pdf")}
        )
        
        assert create_res.status_code == 201
        data = create_res.json()["data"]
        cand_id = data["id"]
        # When using Cloudinary, resume_url is the cloudinary URL
        assert "cloudinary.com" in data["resume_url"]

        # 2. PATCH USER with New Resume
        updated_content = b"%PDF-1.4\nUpdated Resume Content"
        patch_res = client.patch(
            f"/api/admin/users/{cand_id}",
            headers=auth_headers,
            data={"full_name": "Updated Direct Name"},
            files={"resume": ("updated.pdf", io.BytesIO(updated_content), "application/pdf")}
        )
        
        assert patch_res.status_code == 200
        patch_data = patch_res.json()["data"]
        assert patch_data["full_name"] == "Updated Direct Name"

        # Verify user has resume_path in DB (should be the mock URL)
        from app.models.db_models import User
        user = session.get(User, cand_id)
        assert user.resume_path == "https://mock-cloudinary.com/resume.pdf"

        # 3. VERIFY DOWNLOAD (Fallback to local or redirect)
        # Note: In current implementation, /api/resume/ redirects or returns the path.
        # If it's a URL, it might redirect.
        get_res = client.get("/api/resume/", params={"user_id": str(cand_id)}, headers=auth_headers)
        # Depending on implementation, this might be a 302 redirect or 200 with the URL content
        # For now, we just check if it doesn't crash
        assert get_res.status_code in [200, 302, 307]
