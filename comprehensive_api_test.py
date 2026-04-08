#!/usr/bin/env python3
"""
Comprehensive API testing script to test all 56 endpoints
"""

import requests
import json
import time
from typing import Dict, List, Tuple

class ComprehensiveAPITester:
    def __init__(self, base_url: str = "https://ai-interview-backend-d7t1.onrender.com"):
        self.base_url = base_url
        self.admin_token = None
        self.candidate_token = None
        self.results = []
        
    def get_admin_token(self):
        """Get admin authentication token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data="username=admin@test.com&password=admin123"
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                print(f"✅ Admin token obtained")
                return True
            else:
                print(f"❌ Admin token failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin token error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, files: Dict = None, params: Dict = None, use_admin: bool = True) -> Dict:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if use_admin and self.admin_token:
            headers["Authorization"] = f"Bearer {self.admin_token}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            
            end_time = time.time()
            response_time = round(end_time - start_time, 3)
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "response_time": response_time,
                "success": response.status_code < 400,
                "content_length": len(response.content),
                "error": None
            }
            
            # Check for specific error patterns
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    result["error"] = error_data.get("message", "Unknown error")
                except:
                    result["error"] = response.text[:100]
            
            return result
            
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time": 0,
                "success": False,
                "content_length": 0,
                "error": str(e)
            }
    
    def run_comprehensive_tests(self):
        """Run tests on all endpoints"""
        print("🚀 Starting Comprehensive API Testing")
        print("=" * 60)
        
        # Get authentication token
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return
        
        # Define all endpoints to test
        endpoints = [
            # Authentication endpoints
            ("GET", "/api/auth/me", None),
            ("POST", "/api/auth/logout", None),
            ("POST", "/api/auth/login", {"email": "admin@test.com", "password": "admin123"}),
            ("POST", "/api/auth/register", {"email": "test@example.com", "password": "test123", "full_name": "Test User"}),
            
            # Admin endpoints - Users
            ("GET", "/api/admin/users", None),
            ("GET", "/api/admin/users/results", None),
            ("GET", "/api/admin/candidates", None),
            
            # Admin endpoints - Papers
            ("GET", "/api/admin/papers", None),
            ("GET", "/api/admin/questions", None),
            ("POST", "/api/admin/generate-paper", {"ai_prompt": "Test prompt", "years_of_experience": 3, "num_questions": 2}),
            ("POST", "/api/admin/generate-coding-paper", {"ai_prompt": "Test coding", "difficulty_mix": "Easy", "num_questions": 2}),
            
            # Admin endpoints - Interviews
            ("GET", "/api/admin/interviews", None),
            ("POST", "/api/admin/interviews/schedule", {"candidate_user_id": 1, "paper_id": 1, "schedule_time": "2026-04-09T10:00:00Z"}),
            ("GET", "/api/admin/interviews/live-status", None),
            
            # Admin endpoints - Coding Papers
            ("GET", "/api/admin/coding-papers/", None),
            
            # Interview endpoints
            ("GET", "/api/interview/tts", {"text": "test", "folder": "test"}),
            ("POST", "/api/interview/tools/speech-to-text", None),  # Will test with file separately
            ("POST", "/api/interview/tools/sttEvaluate", None),   # Will test with file separately
            
            # Status endpoints
            ("GET", "/api/status/", None),
            
            # Resume endpoints
            ("GET", "/api/resume/", None),
            
            # Teams endpoints
            ("GET", "/api/super-admin/teams", None),
        ]
        
        print(f"📋 Testing {len(endpoints)} endpoints...")
        print()
        
        # Test each endpoint
        for i, (method, endpoint, data) in enumerate(endpoints, 1):
            print(f"[{i:2d}/{len(endpoints)}] {method:4s} {endpoint}")
            result = self.test_endpoint(method, endpoint, data)
            self.results.append(result)
            
            if result["success"]:
                print(f"      ✅ {result['status_code']} - {result['response_time']}s")
            else:
                print(f"      ❌ {result['status_code']} - {result['error'] or 'Unknown error'}")
        
        # Test file upload endpoints separately
        print("\n📁 Testing file upload endpoints...")
        self.test_file_endpoints()
        
        # Test endpoints with parameters
        print("\n🔗 Testing parameterized endpoints...")
        self.test_parameterized_endpoints()
        
        # Generate summary report
        self.generate_report()
    
    def test_file_endpoints(self):
        """Test endpoints that require file uploads"""
        # Create a test file
        test_file_content = b"test audio content"
        
        file_endpoints = [
            ("POST", "/api/interview/tools/speech-to-text", "audio", test_file_content),
            ("POST", "/api/interview/tools/sttEvaluate", "audio", test_file_content),
        ]
        
        for method, endpoint, file_field, file_content in file_endpoints:
            print(f"      {method:4s} {endpoint}")
            files = {file_field: ("test.wav", file_content, "audio/wav")}
            result = self.test_endpoint(method, endpoint, files=files)
            self.results.append(result)
            
            if result["success"]:
                print(f"         ✅ {result['status_code']} - {result['response_time']}s")
            else:
                print(f"         ❌ {result['status_code']} - {result['error'] or 'Unknown error'}")
    
    def test_parameterized_endpoints(self):
        """Test endpoints that require path parameters"""
        # These would need actual IDs from the database
        param_endpoints = [
            ("GET", "/api/admin/users/1"),
            ("GET", "/api/admin/users/1/check-delete"),
            ("GET", "/api/admin/papers/1"),
            ("GET", "/api/admin/papers/1/questions"),
            ("GET", "/api/admin/questions/1"),
            ("GET", "/api/admin/interviews/1"),
            ("GET", "/api/admin/interviews/1/status"),
            ("GET", "/api/admin/results/1"),
            ("GET", "/api/admin/coding-papers/1"),
            ("GET", "/api/admin/coding-papers/1/questions"),
            ("GET", "/api/super-admin/teams/1"),
        ]
        
        for method, endpoint in param_endpoints:
            print(f"      {method:4s} {endpoint}")
            result = self.test_endpoint(method, endpoint)
            self.results.append(result)
            
            if result["success"]:
                print(f"         ✅ {result['status_code']} - {result['response_time']}s")
            else:
                print(f"         ❌ {result['status_code']} - {result['error'] or 'Unknown error'}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE API TESTING REPORT")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print()
        
        # Categorize results
        status_codes = {}
        for result in self.results:
            code = result["status_code"]
            status_codes[code] = status_codes.get(code, 0) + 1
        
        print("📋 Status Code Distribution:")
        for code in sorted(status_codes.keys()):
            status = "✅" if code < 400 else "❌"
            print(f"   {status} {code}: {status_codes[code]} endpoints")
        
        print()
        print("❌ Failed Endpoints:")
        failed_endpoints = [r for r in self.results if not r["success"]]
        for result in failed_endpoints:
            print(f"   {result['method']:4s} {result['endpoint']}")
            print(f"      Error: {result['error'] or 'Unknown error'}")
        
        # Performance analysis
        avg_response_time = sum(r["response_time"] for r in self.results if r["success"]) / max(successful_tests, 1)
        print(f"\n⚡ Average Response Time: {avg_response_time:.3f}s")
        
        slow_endpoints = [r for r in self.results if r["success"] and r["response_time"] > 5.0]
        if slow_endpoints:
            print(f"🐌 Slow Endpoints (>5s):")
            for result in sorted(slow_endpoints, key=lambda x: x["response_time"], reverse=True):
                print(f"   {result['response_time']:.1f}s - {result['method']:4s} {result['endpoint']}")

if __name__ == "__main__":
    tester = ComprehensiveAPITester()
    tester.run_comprehensive_tests()
