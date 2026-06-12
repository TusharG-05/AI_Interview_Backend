from fastapi.testclient import TestClient
from app.server import app
from app.core.database import get_db, engine
from sqlmodel import Session, select
from app.models.db_models import User, UserRole, InterviewSession
from app.auth.security import create_access_token
import json
import logging

logging.basicConfig(level=logging.DEBUG)

def test_websockets():
    client = TestClient(app)
    
    with Session(engine) as session:
        # Create a mock admin and candidate if needed, or just fetch the first ones
        admin = session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
        candidate = session.exec(select(User).where(User.role == UserRole.CANDIDATE)).first()
        
        if not admin:
            admin = User(email="test_admin@example.com", role=UserRole.ADMIN)
            session.add(admin)
            session.commit()
            session.refresh(admin)
            
        if not candidate:
            candidate = User(email="test_candidate@example.com", role=UserRole.CANDIDATE)
            session.add(candidate)
            session.commit()
            session.refresh(candidate)
            
        # Create a test interview
        interview = session.exec(select(InterviewSession)).first()
        if not interview:
            from datetime import datetime
            interview = InterviewSession(admin_id=admin.id, candidate_id=candidate.id, schedule_time=datetime.utcnow())
            session.add(interview)
            session.commit()
            session.refresh(interview)
            
        admin_token = create_access_token(data={"sub": admin.email, "role": admin.role})
        candidate_token = create_access_token(data={"sub": candidate.email, "role": candidate.role})
        interview_id = interview.id

    print("\n--- Testing Global Admin WS ---")
    try:
        with client.websocket_connect(f"/api/admin/dashboard/ws?token={admin_token}") as websocket:
            print("✅ Global Admin WS Connected successfully!")
            # Should be connected, let's try sending a ping or just observe it didn't crash
    except Exception as e:
        print(f"❌ Global Admin WS Failed: {e}")

    print("\n--- Testing Candidate Interview WS ---")
    try:
        with client.websocket_connect(f"/ws/api/interview/{interview_id}?token={candidate_token}") as websocket:
            print("✅ Candidate Interview WS Connected successfully!")
    except Exception as e:
        print(f"❌ Candidate Interview WS Failed: {e}")
        
    print("\n--- Testing Per-Interview Admin WS ---")
    try:
        with client.websocket_connect(f"/ws/api/dashboard/{interview_id}?token={admin_token}") as websocket:
            print("✅ Per-Interview Admin WS Connected successfully!")
    except Exception as e:
        print(f"❌ Per-Interview Admin WS Failed: {e}")

if __name__ == "__main__":
    test_websockets()
