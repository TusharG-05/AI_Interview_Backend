import requests
import os
import uuid

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename):
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n% dummy content")

def test_direct_upload_in_admin_apis():
    print("Starting Direct Resume Upload in Admin APIs Tests...")

    # 1. Login as Admin
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS
    })
    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" Admin Logged In")

    pdf_path = "direct_upload.pdf"
    create_test_pdf(pdf_path)

    try:
        # 2. CREATE USER with Direct Resume Upload
        cand_email = f"direct_{uuid.uuid4().hex[:6]}@test.com"
        with open(pdf_path, "rb") as f:
            create_res = requests.post(
                f"{BASE_URL}/admin/users",
                headers=admin_headers,
                data={
                    "email": cand_email,
                    "full_name": "Direct Upload Candidate",
                    "password": "password123",
                    "role": "CANDIDATE"
                },
                files={"resume": ("my_initial_resume.pdf", f, "application/pdf")}
            )
        
        assert create_res.status_code == 201, f"Create failed: {create_res.text}"
        data = create_res.json()["data"]
        cand_id = data["id"]
        assert data["resume_filename"] == "my_initial_resume.pdf"
        assert data["resume_url"] == f"/api/resume/{cand_id}"
        print(f" Created User with Direct Resume SUCCESS (ID: {cand_id})")

        # 3. PATCH USER with Direct Resume Replace
        with open(pdf_path, "rb") as f:
            patch_res = requests.patch(
                f"{BASE_URL}/admin/users/{cand_id}",
                headers=admin_headers,
                data={"full_name": "Updated Direct Name"},
                files={"resume": ("updated_resume.pdf", f, "application/pdf")}
            )
        
        assert patch_res.status_code == 200, f"Patch failed: {patch_res.text}"
        patch_data = patch_res.json()["data"]
        assert patch_data["full_name"] == "Updated Direct Name"
        assert patch_data["resume_filename"] == "updated_resume.pdf"
        print(" Updated User with Direct Resume Replacement SUCCESS")

        # 4. Verify Download
        get_res = requests.get(f"{BASE_URL}/resume/{cand_id}", headers=admin_headers)
        assert get_res.status_code == 200
        assert get_res.headers["content-type"] == "application/pdf"
        print(" Verified Resume Download SUCCESS")

        print("\nALL DIRECT RESUME UPLOAD TESTS PASSED!")
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

if __name__ == "__main__":
    test_direct_upload_in_admin_apis()
