
import pytest
from app.models.db_models import UserRole, InterviewStatus
from datetime import datetime, timezone, timedelta

def test_admin_paper_management(client, session, auth_headers):
    """Test full CRUD cycle for question papers."""
    # 1. Create Paper
    paper_data = {"name": "Senior Python Backend", "description": "High level concepts"}
    response = client.post("/api/admin/papers", json=paper_data, headers=auth_headers)
    assert response.status_code == 201
    paper_id = response.json()["data"]["id"]

    # 2. Get Paper
    response = client.get(f"/api/admin/papers/{paper_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Senior Python Backend"

    # 3. Update Paper
    response = client.patch(f"/api/admin/papers/{paper_id}", json={"name": "Updated Python Paper"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Python Paper"

    # 4. List Papers
    response = client.get("/api/admin/papers", headers=auth_headers)
    assert response.status_code == 200
    assert any(p["id"] == paper_id for p in response.json()["data"])

    # 5. Delete Paper
    response = client.delete(f"/api/admin/papers/{paper_id}", headers=auth_headers)
    assert response.status_code == 200
    
    # 6. Verify Deletion
    response = client.get(f"/api/admin/papers/{paper_id}", headers=auth_headers)
    assert response.status_code == 404

def test_admin_question_management(client, session, auth_headers):
    """Test adding and managing questions within a paper."""
    # Setup paper
    paper_res = client.post("/api/admin/papers", json={"name": "Q-Test Paper"}, headers=auth_headers)
    paper_id = paper_res.json()["data"]["id"]

    # 1. Add Question
    q_data = {
        "content": "Explain GIL in Python.",
        "topic": "Core",
        "difficulty": "Hard",
        "marks": 15,
        "response_type": "text"
    }
    response = client.post(f"/api/admin/papers/{paper_id}/questions", json=q_data, headers=auth_headers)
    assert response.status_code == 201
    q_id = response.json()["data"]["id"]

    # 2. Get Questions for Paper
    response = client.get(f"/api/admin/papers/{paper_id}/questions", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1

    # 3. Update Question
    response = client.patch(f"/api/admin/questions/{q_id}", json={"marks": 20}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["marks"] == 20

    # 4. Delete Question
    response = client.delete(f"/api/admin/questions/{q_id}", headers=auth_headers)
    assert response.status_code == 200

def test_admin_unauthorized_access(client):
    """Test that admin endpoints are protected."""
    response = client.get("/api/admin/papers")
    assert response.status_code == 401
    
    # login as candidate and try to access admin
    # (Note: In conftest, auth_headers uses admin by default)
    pass # covered by specific tests if needed

def test_admin_invalid_payloads(client, auth_headers):
    """Test 422 errors for malformed admin requests."""
    # Missing required 'name'
    response = client.post("/api/admin/papers", json={"description": "Missing name"}, headers=auth_headers)
    assert response.status_code == 422
