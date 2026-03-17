
import pytest
import io
import uuid
from app.models.db_models import UserRole

def test_direct_upload_workflow(client, session, test_users, auth_headers):
    """Test creating and updating users with direct resume uploads."""
    admin, candidate, super_admin = test_users
    print("Starting Direct Resume Upload Test...")

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
    assert data["resume_url"] == f"/api/resume/{cand_id}"

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

    # Verify user has resume_path in DB
    from app.models.db_models import User
    user = session.get(User, cand_id)
    print(f"User resume_path: {user.resume_path if user else 'User not found'}")
    assert user is not None
    assert user.resume_path is not None, "User should have resume_path set after PATCH"
    import os
    assert os.path.exists(user.resume_path), f"File should exist at {os.path.abspath(user.resume_path)}"

    # 3. VERIFY DOWNLOAD
    get_res = client.get("/api/resume/", params={"user_id": str(cand_id)}, headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.headers["content-type"] == "application/pdf"
    assert get_res.content == updated_content
