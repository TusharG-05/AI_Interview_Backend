
import requests
import json
import time

BASE_URL = "https://localhost:8001"
# Credentials for testing
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123" 

# User provided token for testing
PROVIDED_TOKEN = None

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False # Disable verification for self-signed certs
        self.results = []
        self.token = PROVIDED_TOKEN
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def log_result(self, category, name, url, response):
        success = response.status_code < 400
        result = {
            "category": category,
            "name": name,
            "url": url,
            "status_code": response.status_code,
            "success": success,
            "message": response.text[:200] if not success else "OK"
        }
        self.results.append(result)
        status_str = "✅ PASS" if success else "❌ FAIL"
        print(f"[{status_str}] {category} - {name} ({response.status_code})")
        if not success:
            print(f"    Error: {result['message']}")

    def login(self):
        url = f"{self.base_url}/api/auth/login"
        payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        try:
            response = self.session.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.token = data["data"]["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"🔑 Logged in as {ADMIN_EMAIL}")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login Exception: {e}")
            return False

    def test_get(self, category, name, path):
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, timeout=10)
            self.log_result(category, name, url, response)
            return response
        except Exception as e:
            print(f"❌ Exception on {name}: {e}")
            return None

    def run_tests(self):
        print(f"🚀 Starting Comprehensive API Tests on {self.base_url}")
        
        # 1. Public Endpoints
        self.test_get("Public", "Swagger Docs", "/docs")
        self.test_get("Public", "Status", "/api/status/?interview_id=1")
        
        # 2. Auth
        if not self.token:
            if not self.login():
                print("❌ Aborting tests due to login failure.")
                return
        else:
            print(f"🔑 Using user-provided token for {ADMIN_EMAIL}")
            # Verify token works
            test_resp = self.session.get(f"{self.base_url}/api/admin/papers")
            if test_resp.status_code == 401:
                print("⚠️ Provided token invalid. Attempting login...")
                if not self.login():
                    print("❌ Aborting tests due to login failure.")
                    return

        # 3. Admin - Papers
        self.test_get("Admin", "List Papers", "/api/admin/papers")
        
        # 4. Admin - Interviews
        self.test_get("Admin", "List Interviews", "/api/admin/interviews")
        self.test_get("Admin", "Interview Detail (137)", "/api/admin/interviews/137")
        self.test_get("Admin", "Interview Live Status", "/api/admin/interviews/live-status")
        
        # 5. Admin - Users
        self.test_get("Admin", "List Users", "/api/admin/users")
        self.test_get("Admin", "List Candidates", "/api/admin/candidates")
        self.test_get("Admin", "List Results", "/api/admin/users/results")
        
        # 6. Admin - Teams
        self.test_get("Admin", "List Teams", "/api/super-admin/teams")
        
        # 7. Coding Papers
        self.test_get("Coding", "List Coding Papers", "/api/admin/coding-papers/")

        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        failed = [r for r in self.results if not r["success"]]
        if not failed:
            print("🟢 ALL TESTED ENDPOINTS ARE FUNCTIONAL")
        else:
            print(f"🔴 {len(failed)} ENDPOINTS FAILED:")
            for r in failed:
                print(f"  - {r['category']}: {r['name']} ({r['status_code']})")
        print("="*50)

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    tester.run_tests()
