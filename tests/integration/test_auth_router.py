
import pytest
from app.models.db_models import User, UserRole
from app.auth.security import get_password_hash
from sqlmodel import select

def test_register_bootstrap_user(client, session):
    # Arrange: DB is empty implicitly due to function scope
    
    response = client.post("/api/auth/register", json={
        "email": "admin@example.com",
        "password": "password123",
        "full_name": "Admin User",
        "role": "admin"
    })
    
    assert response.status_code == 200  # HTTP status might still be 200 unless explicitly set
    assert response.json()["status_code"] == 201
    assert response.json()["message"] == "User registered successfully"
    assert "access_token" in response.json()["data"]
    
    # Verify DB persistence
    user = session.exec(select(User).where(User.email == "admin@example.com")).first()
    assert user is not None
    assert user.role == UserRole.ADMIN

def test_login_success(client, session):
    # Arrange: Create user
    hashed = get_password_hash("password123")
    user = User(email="test@example.com", password_hash=hashed, role=UserRole.CANDIDATE, full_name="Test User")
    session.add(user)
    session.commit()
    
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    assert response.json()["status_code"] == 200
    assert response.json()["message"] == "Login successfully"
    assert response.json()["data"]["email"] == "test@example.com"

def test_login_failure(client, session):
    # Arrange: DB empty (no user)
    
    response = client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 401
