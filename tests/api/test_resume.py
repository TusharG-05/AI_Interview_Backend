import requests
import os
import uuid
import time

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASS = "admin123"

def create_test_pdf(filename):
    # Just a dummy PDF content
    with open(filename, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF")

def test_resume_apis():
    print("Starting Refined Resume API Tests (Optional User ID)...")

    # 1. AUTH: Login as Super Admin
    try:
        login_res = requests.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASS
        })
        if login_res.status_code != 200:
            print(f"FAILED: Admin login failed {login_res.status_code}: {login_res.text}")
            return
    except Exception as e:
        print(f"FAILED: Could not connect to server: {e}")
        return

    admin_token = login_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" Super Admin Logged In")

    # 2. Register two candidates
    cand1_email = f"cand1_{uuid.uuid4().hex[:6]}@test.com"
    cand2_email = f"cand2_{uuid.uuid4().hex[:6]}@test.com"
    passw = "admin123"

    reg1 = requests.post(f"{BASE_URL}/auth/register", headers=admin_headers, json={
        "email": cand1_email, "password": passw, "full_name": "Candidate One", "role": "CANDIDATE"
    })
    cand1_id = reg1.json()["data"]["id"]
    cand1_token = reg1.json()["data"]["access_token"]
    cand1_headers = {"Authorization": f"Bearer {cand1_token}"}

    reg2 = requests.post(f"{BASE_URL}/auth/register", headers=admin_headers, json={
        "email": cand2_email, "password": passw, "full_name": "Candidate Two", "role": "CANDIDATE"
    })
    cand2_id = reg2.json()["data"]["id"]
    cand2_token = reg2.json()["data"]["access_token"]
    cand2_headers = {"Authorization": f"Bearer {cand2_token}"}
    print(f" Created Candidates: {cand1_id}, {cand2_id}")

    # 3. Create test PDF
    pdf_path = "test_resume.pdf"
    create_test_pdf(pdf_path)

    try:
        # 4. CANDIDATE 1: Upload Resume WITHOUT ID (Should work)
        with open(pdf_path, "rb") as f:
            up_res = requests.post(f"{BASE_URL}/resume/upload", headers=cand1_headers, files={"file": ("resume.pdf", f, "application/pdf")})
        assert up_res.status_code == 201, f"Upload failed: {up_res.text}"
        print(" Candidate 1 Uploaded Own Resume (NO ID) SUCCESS")

        # 5. CANDIDATE 1: Get Resume WITHOUT ID (Should work)
        get_res = requests.get(f"{BASE_URL}/resume", headers=cand1_headers)
        assert get_res.status_code == 200
        assert get_res.headers["content-type"] == "application/pdf"
        print(" Candidate 1 Retrieved Own Resume (NO ID) SUCCESS")

        # 6. ADMIN: Upload Resume FOR CANDIDATE 2 WITH ID (Should work)
        with open(pdf_path, "rb") as f:
            admin_up_res = requests.post(f"{BASE_URL}/resume/upload/{cand2_id}", headers=admin_headers, files={"file": ("admin_upload.pdf", f, "application/pdf")})
        assert admin_up_res.status_code == 201
        print(" Admin Uploaded Resume for Candidate 2 (WITH ID) SUCCESS")

        # 7. CANDIDATE 2: Get Own Resume WITHOUT ID (Should work)
        c2_get = requests.get(f"{BASE_URL}/resume", headers=cand2_headers)
        assert c2_get.status_code == 200
        print(" Candidate 2 Retrieved Own Resume (Admin Uploaded, NO ID) SUCCESS")

        # 8. CANDIDATE 2: Try to get Candidate 1's Resume WITH ID (Should FAIL)
        fail_get = requests.get(f"{BASE_URL}/resume/{cand1_id}", headers=cand2_headers)
        assert fail_get.status_code == 403
        print(" Candidate 2 Accessing Candidate 1 Resume DENIED (Correct)")

        # 9. CANDIDATE 1: Patch Resume WITHOUT ID
        with open(pdf_path, "rb") as f:
            patch_res = requests.patch(f"{BASE_URL}/resume", headers=cand1_headers, files={"file": ("new_resume.pdf", f, "application/pdf")})
        assert patch_res.status_code == 220
        print(" Candidate 1 Patched Own Resume (NO ID) SUCCESS")

        # 10. ADMIN: Delete Candidate 1's Resume WITH ID
        del_res = requests.delete(f"{BASE_URL}/resume/{cand1_id}", headers=admin_headers)
        assert del_res.status_code == 200
        print(" Admin Deleted Candidate 1 Resume (WITH ID) SUCCESS")

        # 11. CANDIDATE 2: Delete Own Resume WITHOUT ID
        del2_res = requests.delete(f"{BASE_URL}/resume", headers=cand2_headers)
        assert del2_res.status_code == 200
        print(" Candidate 2 Deleted Own Resume (NO ID) SUCCESS")

        # 12. Verify Deletions
        v1 = requests.get(f"{BASE_URL}/resume", headers=cand1_headers)
        assert v1.status_code == 404
        v2 = requests.get(f"{BASE_URL}/resume", headers=cand2_headers)
        assert v2.status_code == 404
        print(" Verified All Deletions SUCCESS")

        print("\nALL REFINED RESUME API TESTS PASSED!")
    finally:
        # Cleanup test file
        if os.path.exists(pdf_path): os.remove(pdf_path)

if __name__ == "__main__":
    test_resume_apis()
