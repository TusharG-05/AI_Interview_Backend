#!/usr/bin/env python3
"""
Comprehensive API Health Check Script
Tests all endpoints and generates a health report
"""
import requests
import json
from typing import Dict, List, Tuple
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

class APIHealthChecker:
    def __init__(self):
        self.results = []
        self.token = None
        
    def login(self) -> bool:
        """Get admin token for authenticated requests"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "admin@test.com", "password": "admin123"},
                timeout=10
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                print(f"{GREEN}✓{RESET} Authentication successful")
                return True
            else:
                print(f"{RED}✗{RESET} Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"{RED}✗{RESET} Authentication error: {e}")
            return False
    
    def test_endpoint(self, method: str, path: str, requires_auth: bool = True, 
                     data: dict = None, files: dict = None) -> Tuple[int, str]:
        """Test a single endpoint and return status code and message"""
        url = f"{BASE_URL}{path}"
        headers = {}
        
        if requires_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, files=files, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return 0, f"Unknown method: {method}"
            
            return response.status_code, response.text[:100]
        except requests.exceptions.Timeout:
            return 0, "Timeout"
        except requests.exceptions.ConnectionError:
            return 0, "Connection Error"
        except Exception as e:
            return 0, str(e)[:100]
    
    def run_tests(self):
        """Run all endpoint tests"""
        print(f"\n{'='*60}")
        print(f"API Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Auth Endpoints
        print(f"\n{YELLOW}[Auth Endpoints]{RESET}")
        auth_tests = [
            ("POST", "/api/auth/login", False),
            ("POST", "/api/auth/logout", True),
            ("GET", "/api/auth/me", True),
        ]
        for method, path, auth in auth_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Auth", method, path, status, msg)
        
        # Admin - Papers
        print(f"\n{YELLOW}[Admin - Papers]{RESET}")
        admin_paper_tests = [
            ("GET", "/api/admin/papers", True),
            ("GET", "/api/admin/papers/1", True),
            ("GET", "/api/admin/papers/1/questions", True),
        ]
        for method, path, auth in admin_paper_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Admin-Papers", method, path, status, msg)
        
        # Admin - Questions
        print(f"\n{YELLOW}[Admin - Questions]{RESET}")
        admin_question_tests = [
            ("GET", "/api/admin/questions", True),
        ]
        for method, path, auth in admin_question_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Admin-Questions", method, path, status, msg)
        
        # Admin - Interviews
        print(f"\n{YELLOW}[Admin - Interviews]{RESET}")
        admin_interview_tests = [
            ("GET", "/api/admin/interviews", True),
            ("GET", "/api/admin/interviews/live-status", True),
        ]
        for method, path, auth in admin_interview_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Admin-Interviews", method, path, status, msg)
        
        # Admin - Users
        print(f"\n{YELLOW}[Admin - Users]{RESET}")
        admin_user_tests = [
            ("GET", "/api/admin/users", True),
            ("GET", "/api/admin/candidates", True),
        ]
        for method, path, auth in admin_user_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Admin-Users", method, path, status, msg)
        
        # Interview Endpoints
        print(f"\n{YELLOW}[Interview Endpoints]{RESET}")
        interview_tests = [
            ("GET", "/api/interview/tts?text=test", True),
        ]
        for method, path, auth in interview_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Interview", method, path, status, msg)
        
        # Candidate Endpoints
        print(f"\n{YELLOW}[Candidate Endpoints]{RESET}")
        candidate_tests = [
            ("GET", "/api/candidate/history", True),
        ]
        for method, path, auth in candidate_tests:
            status, msg = self.test_endpoint(method, path, auth)
            self._log_result("Candidate", method, path, status, msg)
        
        self._print_summary()
    
    def _log_result(self, category: str, method: str, path: str, status: int, msg: str):
        """Log and print test result"""
        result = {
            "category": category,
            "method": method,
            "path": path,
            "status": status,
            "message": msg
        }
        self.results.append(result)
        
        # Determine status symbol
        if status == 0:
            symbol = f"{RED}✗{RESET}"
            status_text = "ERROR"
        elif 200 <= status < 300:
            symbol = f"{GREEN}✓{RESET}"
            status_text = f"{status}"
        elif 400 <= status < 500:
            symbol = f"{YELLOW}⚠{RESET}"
            status_text = f"{status}"
        else:
            symbol = f"{RED}✗{RESET}"
            status_text = f"{status}"
        
        print(f"{symbol} {method:6} {path:50} [{status_text}]")
    
    def _print_summary(self):
        """Print test summary"""
        total = len(self.results)
        success = len([r for r in self.results if 200 <= r["status"] < 300])
        client_errors = len([r for r in self.results if 400 <= r["status"] < 500])
        server_errors = len([r for r in self.results if 500 <= r["status"] < 600])
        connection_errors = len([r for r in self.results if r["status"] == 0])
        
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Total Endpoints Tested: {total}")
        print(f"  {GREEN}✓{RESET} Success (2xx):        {success}")
        print(f"  {YELLOW}⚠{RESET} Client Errors (4xx):  {client_errors}")
        print(f"  {RED}✗{RESET} Server Errors (5xx):  {server_errors}")
        print(f"  {RED}✗{RESET} Connection Errors:    {connection_errors}")
        print(f"{'='*60}\n")
        
        # Save detailed report
        with open("api_health_report.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "success": success,
                    "client_errors": client_errors,
                    "server_errors": server_errors,
                    "connection_errors": connection_errors
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"Detailed report saved to: api_health_report.json\n")

if __name__ == "__main__":
    checker = APIHealthChecker()
    if checker.login():
        checker.run_tests()
    else:
        print(f"{RED}Failed to authenticate. Cannot proceed with tests.{RESET}")
