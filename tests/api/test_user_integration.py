import requests
import os
import uuid

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename):
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n% dummy content")

def test_user_api_integration():
    print("Starting User API Resume Integration Tests...")

    # 1. Login as Admin
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS
    })
    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" Admin Logged In")

    # 2. Register a candidate
    cand_email = f"cand_int_{uuid.uuid4().hex[:6]}@test.com"
    reg = requests.post(f"{BASE_URL}/auth/register", headers=admin_headers, json={
        "email": cand_email, "password": "password123", "full_name": "Integrated Candidate", "role": "CANDIDATE"
    })
    cand_id = reg.json()["data"]["id"]
    cand_token = reg.json()["data"]["access_token"]
    cand_headers = {"Authorization": f"Bearer {cand_token}"}
    print(f" Candidate Created: {cand_id}")

    # 3. Check Admin GET User BEFORE upload
    get_res = requests.get(f"{BASE_URL}/admin/users/{cand_id}", headers=admin_headers)
    user_data = get_res.json()["data"]
    assert "resume_filename" in user_data
    assert "resume_url" in user_data
    assert user_data["resume_filename"] is None
    assert user_data["resume_url"] is None
    print(" Verified fields exist (but null) BEFORE upload SUCCESS")

    # 4. Upload Resume for Candidate
    pdf_path = "int_test.pdf"
    create_test_pdf(pdf_path)
    with open(pdf_path, "rb") as f:
        requests.post(f"{BASE_URL}/resume/upload/{cand_id}", headers=admin_headers, files={"file": ("my_resume.pdf", f, "application/pdf")})
    print(" Resume Uploaded")

    # 5. Check Admin GET User AFTER upload
    get_res_after = requests.get(f"{BASE_URL}/admin/users/{cand_id}", headers=admin_headers)
    data_after = get_res_after.json()["data"]
    assert data_after["resume_filename"] == "my_resume.pdf"
    assert data_after["resume_url"] == f"/api/resume/{cand_id}"
    print(" Verified Administrative User Detail contains resume info SUCCESS")

    # 6. Check Auth /me AFTER upload
    me_res = requests.get(f"{BASE_URL}/auth/me", headers=cand_headers)
    me_data = me_res.json()["data"]
    assert me_data["resume_filename"] == "my_resume.pdf"
    assert me_data["resume_url"] == f"/api/resume/{cand_id}"
    print(" Verified Auth /me contains resume info SUCCESS")

    # 7. Check List Users
    list_res = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    found = False
    for u in list_res.json()["data"]:
        if u["id"] == cand_id:
            assert u["resume_filename"] == "my_resume.pdf"
            assert u["resume_url"] == f"/api/resume/{cand_id}"
            found = True
    assert found
    print(" Verified List Users contains resume info SUCCESS")

    # Cleanup
    if os.path.exists(pdf_path): os.remove(pdf_path)
    print("\nALL USER API INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    test_user_api_integration()
