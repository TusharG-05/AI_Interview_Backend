import requests
import os
import uuid

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename):
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n% dummy content")

def test_simplified_resume_api():
    print("Starting Simplified Resume API Tests...")

    # 1. Login as Admin
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS
    })
    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_id = login_res.json()["data"]["id"]
    print(f" Admin Logged In (ID: {admin_id})")

    pdf_path = "simplified_test.pdf"
    create_test_pdf(pdf_path)

    try:
        # 2. Register a candidate (gets token immediately)
        cand_email = f"simple_{uuid.uuid4().hex[:6]}@test.com"
        reg_res = requests.post(f"{BASE_URL}/auth/register", headers=admin_headers, json={
            "email": cand_email, "password": "password123", "full_name": "Simple Candidate", "role": "CANDIDATE"
        })
        assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
        cand_data = reg_res.json()["data"]
        cand_id = cand_data["id"]
        cand_token = cand_data["access_token"]
        cand_headers = {"Authorization": f"Bearer {cand_token}"}
        print(f" Candidate Registered (ID: {cand_id})")

        # 3. Upload Resume for Candidate using Admin PATCH API
        with open(pdf_path, "rb") as f:
            patch_res = requests.patch(
                f"{BASE_URL}/admin/users/{cand_id}",
                headers=admin_headers,
                files={"resume": ("my_simple_resume.pdf", f, "application/pdf")}
            )
        assert patch_res.status_code == 200, f"Patch failed: {patch_res.text}"
        print(" Resume Uploaded for Candidate via Admin Patch")

        # 4. GET Own Resume (no user_id param)
        get_self = requests.get(f"{BASE_URL}/resume/", headers=cand_headers)
        assert get_self.status_code == 200, f"Get self failed: {get_self.text}"
        assert get_self.headers["content-type"] == "application/pdf"
        print(" Candidate GET Own Resume (No Param) SUCCESS")

        # 5. GET Own Resume (with user_id param)
        get_self_id = requests.get(f"{BASE_URL}/resume/", headers=cand_headers, params={"user_id": cand_id})
        assert get_self_id.status_code == 200
        print(" Candidate GET Own Resume (With Param) SUCCESS")

        # 6. GET Admin Resume (Forbidden)
        get_other = requests.get(f"{BASE_URL}/resume/", headers=cand_headers, params={"user_id": admin_id})
        assert get_other.status_code == 403
        print(" Candidate GET Admin Resume (Cross-Access) DENIED SUCCESS")

        # 7. Admin GET Candidate Resume
        get_cand_as_admin = requests.get(f"{BASE_URL}/resume/", headers=admin_headers, params={"user_id": cand_id})
        assert get_cand_as_admin.status_code == 200
        print(" Admin GET Candidate Resume SUCCESS")

        # 8. Check non-existent user
        get_fake = requests.get(f"{BASE_URL}/resume/", headers=admin_headers, params={"user_id": 999999})
        assert get_fake.status_code == 404
        print(" GET Non-existent User 404 SUCCESS")

        print("\nALL SIMPLIFIED RESUME API TESTS PASSED!")
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

if __name__ == "__main__":
    test_simplified_resume_api()
