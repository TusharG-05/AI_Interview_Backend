from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlmodel import Session, select
from app.server import app
from app.core.database import get_db
from app.models.db_models import User, InterviewRoom, InterviewSession, Question
import pytest

client = TestClient(app)

# Mock DB Session
@pytest.fixture(name="session")
def session_fixture():
    from app.core.database import engine
    with Session(engine) as session:
        yield session

def test_join_room_atomicity(session):
    """
    Simulates a failure during question assignment (after session creation).
    Verifies that the session is ROLLED BACK and does not exist in DB.
    """
    # 1. Setup Data
    user = User(email="acid_test@example.com", full_name="ACID Tester", password_hash="hash", role="candidate")
    room = InterviewRoom(room_code="ACID_ROOM", password="123", is_active=True, created_by=1, question_count=2)
    session.add(user)
    session.add(room)
    session.commit()
    session.refresh(user)
    session.refresh(room)

    # 2. Mock Authed User
    app.dependency_overrides[get_db] = lambda: session
    
    # Mock token or dependency overrides for user (Simplification: we assume we can inject user)
    # Actually, let's use a simpler approach: Mock the router's dependencies
    from app.routers.candidate import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    # 3. Inject Failure
    # We patch 'random.sample' to raise an exception, simulates error in logic block
    with patch("random.sample", side_effect=Exception("Simulated Failure")):
        response = client.post(
            "/api/candidate/join", 
            json={"room_code": "ACID_ROOM", "password": "123"}
        )
    
    # 4. Assertions
    assert response.status_code == 500
    
    # CRITICAL CHECK: Verify Session does NOT exist
    db_session = session.exec(select(InterviewSession).where(InterviewSession.candidate_id == user.id)).first()
    assert db_session is None, "ACID Violation: Session created despite transaction failure!"

def test_start_interview_atomicity(session):
    """
    Simulates failure during audio upload.
    Verifies that the created InterviewSession is rolled back.
    """
    # Setup
    # Override user mock...
    
    # Mock failure in audio saving
    with patch("app.services.audio.AudioService.save_audio_blob", side_effect=Exception("Disk Full")):
        # We need to act as 'admin' or just pass auth? start_interview endpoint doesn't require auth in code?
        # Checking router... start_interview takes (session_db). No auth dependency? 
        # Ah, looking at code: `candidate_name: str`, `enrollment_audio`. No `current_user`.
        
        with open("tools/test_assets/selfie.jpg", "rb") as f: # Use dummy file
            response = client.post(
                "/api/interview/start",
                data={"candidate_name": "ACID Candidate"},
                files={"enrollment_audio": ("test.wav", f, "audio/wav")}
            )
            
    assert response.status_code == 500
    
    # Verify No Session
    s = session.exec(select(InterviewSession).where(InterviewSession.candidate_name == "ACID Candidate")).first()
    assert s is None, "ACID Violation: Session persisted despite audio failure!"
