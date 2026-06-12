import requests
import json

BASE_URL = "http://localhost:8000"

def audit():
    try:
        res = requests.get(f"{BASE_URL}/openapi.json")
        openapi = res.json()
    except Exception as e:
        print("Could not fetch OpenAPI schema:", e)
        return

    paths = openapi.get("paths", {})
    issues = []
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            # Check for security
            security = operation.get("security")
            # Exclude auth and public endpoints
            if not security and not any(public_path in path for public_path in ["/auth/", "/status", "/credentials", "/otp", "/tts"]):
                # Websockets might not show security in OpenAPI, but check standard endpoints
                issues.append(f"[Missing Auth] {method.upper()} {path} does not require authentication")

            # Check for generic dict responses instead of typed responses
            responses = operation.get("responses", {})
            success_resp = responses.get("200") or responses.get("201")
            
            # This is a bit noisy, so maybe focus on just schema mismatches that are hardcoded or obvious.
            
    print("Potential Issues Found:")
    for issue in issues:
        print(issue)
        
    # Specifically looking for POST /admin/papers missing auth
    papers_post = paths.get("/api/admin/papers", {}).get("post", {})
    if not papers_post.get("security"):
        print("\nCONFIRMED: POST /api/admin/papers is missing authentication!")

if __name__ == "__main__":
    audit()
