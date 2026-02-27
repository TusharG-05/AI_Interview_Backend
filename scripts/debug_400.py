import httpx

def test_add_question():
    client = httpx.Client(base_url="http://127.0.0.1:8001/api")
    
    # 1. Login
    resp = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Paper
    resp = client.post("/admin/papers", headers=headers, json={"name": "Debug Paper"})
    paper_id = resp.json()["data"]["id"]
    print(f"Paper Created: {paper_id}")
    
    # 3. Add Question
    resp = client.post(f"/admin/papers/{paper_id}/questions", headers=headers, json={
        "content": "Test?",
        "topic": "Test",
        "difficulty": "Easy",
        "marks": 1,
        "response_type": "audio"
    })
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    test_add_question()
