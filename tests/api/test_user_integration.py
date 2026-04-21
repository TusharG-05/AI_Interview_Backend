
import pytest
import io
import uuid
from app.models.db_models import UserRole

def test_user_api_integration_workflow(client, session, test_users, auth_headers):
    """
    Test user lifecycle and resume integration:
    - Create user without resume
    - Verify fields are null
    - Upload resume via Admin PATCH
    - Verify fields in User Detail, Auth /me, and List Users
    """
    admin, candidate, super_admin = test_users
    
    # 1. REGISTER Candidate (Needs Auth if not bootstrap)
    cand_email = f"int_{uuid.uuid4().hex[:6]}@test.com"
    reg_res = client.post("/api/auth/register", headers=auth_headers, json={
        "email": cand_email,
        "password": "password123",
        "full_name": "Integrated Cand",
        "role": "CANDIDATE"
    })
    assert reg_res.status_code == 201
    cand_id = reg_res.json()["data"]["id"]
    cand_token = reg_res.json()["data"]["access_token"]
    c_headers = {"Authorization": f"Bearer {cand_token}"}

    # 2. VERIFY Null Resume
    get_res = client.get(f"/api/admin/users/{cand_id}", headers=auth_headers)
    user_data = get_res.json()["data"]
    assert user_data.get("resume_url") is None
    print(" Initial null resume verified")

    # 3. UPLOAD Resume via Admin PATCH
    resume_content = b"%PDF-1.4\nIntegrated Resume"
    upload_res = client.patch(
        f"/api/admin/users/{cand_id}",
        headers=auth_headers,
        files={"resume": ("integrated.pdf", io.BytesIO(resume_content), "application/pdf")}
    )
    assert upload_res.status_code == 200
    print(" Resume uploaded via Patch")

    # 4. VERIFY Auth /me
    me_res = client.get("/api/auth/me", headers=c_headers)
    me_data = me_res.json()["data"]
    assert "resume" in me_data.get("resume_url", "")
    print(" Auth /me verified")

    # 5. VERIFY List Users
    list_res = client.get("/api/admin/users", headers=auth_headers)
    data = list_res.json()["data"]
    users = data["items"] if isinstance(data, dict) and "items" in data else data
    found = any(u["id"] == cand_id and "resume" in u.get("resume_url", "") for u in users)
    assert found
    print(" List users verified")
