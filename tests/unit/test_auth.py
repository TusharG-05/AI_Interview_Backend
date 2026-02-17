def test_register_user(session, client):
    payload = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "password123",
        "role": "candidate"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    
    # Verify DB
    from app.models.db_models import User
    user = session.query(User).filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.full_name == "New User"

def test_login_success(session, client):
    # Create user first
    from app.auth.security import get_password_hash
    from app.models.db_models import User
    
    user = User(
        email="login@example.com",
        full_name="Login User",
        password_hash=get_password_hash("password123")
    )
    session.add(user)
    session.commit()
    
    # Test Login
    payload = {
        "email": "login@example.com",
        "password": "password123"
    }
    response = client.post("/api/auth/login", json=payload) 
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_login_failure(client):
    payload = {
        "email": "nothere@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401

def test_get_me(session, client, auth_headers):
    # Prerequisite: User needs to exist for the token (mocked in fixture) to resolve DB lookup in get_current_user
    # The auth_headers fixture creates a token for "test@example.com"
    # We must ensure that user exists in the session DB
    from app.auth.security import get_password_hash
    from app.models.db_models import User
    user = User(email="test@example.com", full_name="Test User", password_hash=get_password_hash("pass"))
    session.add(user)
    session.commit()
    
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
