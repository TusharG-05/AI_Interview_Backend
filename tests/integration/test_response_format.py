
import pytest
from app.models.db_models import User, UserRole, QuestionPaper, Questions, InterviewSession, InterviewStatus
from app.auth.security import get_password_hash
from sqlmodel import select
from datetime import datetime, timedelta

@pytest.fixture
def admin_user(session):
    user = User(
        email="admin_test@example.com",
        full_name="Admin Test",
        role=UserRole.ADMIN,
        password_hash=get_password_hash("admin123")
    )
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def candidate_user(session):
    user = User(
        email="candidate_test@example.com",
        full_name="Candidate Test",
        role=UserRole.CANDIDATE,
        password_hash=get_password_hash("candidate123")
    )
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def auth_headers(client, admin_user):
    response = client.post("/api/auth/login", json={
        "email": admin_user.email,
        "password": "admin123"
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def candidate_auth_headers(client, candidate_user):
    response = client.post("/api/auth/login", json={
        "email": candidate_user.email,
        "password": "candidate123"
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_papers_response_format(client, session, auth_headers, admin_user):
    # Arrange: Create a paper
    paper = QuestionPaper(name="Test Paper", description="Desc", admin_id=admin_user.id)
    session.add(paper)
    session.commit()

    # Act
    response = client.get("/api/admin/papers", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Check wrapper structure
    assert "status_code" in data
    assert data["status_code"] == 200
    assert "message" in data
    assert "data" in data
    
    # Check content
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    assert data["data"][0]["name"] == "Test Paper"

def test_get_user_response_format(client, session, auth_headers, candidate_user):
    # Act
    response = client.get(f"/api/admin/users/{candidate_user.id}", headers=auth_headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert data["status_code"] == 200
    assert data["message"] == "User details retrieved successfully"
    assert data["data"]["email"] == candidate_user.email
    assert data["data"]["role"] == "candidate"

def test_candidate_history_response_format(client, session, candidate_auth_headers, candidate_user):
    # Act
    response = client.get("/api/candidate/history", headers=candidate_auth_headers)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert data["status_code"] == 200
    assert data["message"] == "Interview history retrieved successfully"
    assert isinstance(data["data"], list)

def test_system_status_response_format(client):
    # Act
    response = client.get("/api/status/?interview_id=1")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert data["status_code"] == 200
    assert data["message"] == "System status retrieved successfully"
    assert data["data"]["status"] == "online"
