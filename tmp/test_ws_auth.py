import asyncio
import pytest
from fastapi.testclient import TestClient
from app.server import app
from app.auth.security import create_access_token
from app.models.db_models import User, UserRole, InterviewSession
from app.core.database import engine, get_db
from sqlmodel import Session, select
from jose import jwt
from datetime import timedelta

client = TestClient(app)

def create_test_user(email: str, role: UserRole):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            user = User(
                email=email,
                role=role,
                full_name=f"Test {role.value}",
                hashed_password="hashed_password",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

def create_test_session(candidate_id: int):
    with Session(engine) as session:
        interview = InterviewSession(
            candidate_id=candidate_id,
            status="scheduled",
            paper_id=1 # Assuming a paper with ID 1 exists or is not strictly validated
        )
        session.add(interview)
        session.commit()
        session.refresh(interview)
        return interview

def get_token(user: User):
    return create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=30))

def test_ws_no_token():
    try:
        with client.websocket_connect("/api/status/ws?interview_id=1") as websocket:
            pytest.fail("Should have raised an error or closed connection")
    except Exception as e:
        # FastAPI TestClient might raise an error when the server closes connection during handshake
        print(f"Caught expected error for no token: {e}")

def test_ws_valid_token_admin():
    admin = create_test_user("admin_ws@example.com", UserRole.ADMIN)
    token = get_token(admin)
    with client.websocket_connect(f"/api/status/ws?interview_id=1&token={token}") as websocket:
        # Should connect successfully
        data = websocket.receive_json()
        assert "warning" in data

def test_ws_candidate_own_session():
    candidate = create_test_user("candidate_ws@example.com", UserRole.CANDIDATE)
    session_obj = create_test_session(candidate.id)
    token = get_token(candidate)
    
    with client.websocket_connect(f"/api/status/ws?interview_id={session_obj.id}&token={token}") as websocket:
        # Should connect successfully
        data = websocket.receive_json()
        assert "warning" in data

def test_ws_candidate_other_session():
    candidate1 = create_test_user("candidate1_ws@example.com", UserRole.CANDIDATE)
    candidate2 = create_test_user("candidate2_ws@example.com", UserRole.CANDIDATE)
    session_obj2 = create_test_session(candidate2.id)
    token1 = get_token(candidate1)
    
    try:
        with client.websocket_connect(f"/api/status/ws?interview_id={session_obj2.id}&token={token1}") as websocket:
            # This should be closed by our logic
            pytest.fail("Should have been forbidden")
    except Exception:
        print("Caught expected error for forbidden session access")

if __name__ == "__main__":
    # Setup test data if needed or run with pytest
    pytest.main([__file__])
