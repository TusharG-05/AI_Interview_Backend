
import pytest
from app.models.db_models import User, UserRole, InterviewSession, InterviewStatus, Questions, InterviewResponse, QuestionPaper
from app.auth.security import get_password_hash
from datetime import datetime, timedelta

@pytest.fixture
def test_setup(session):
    """Creates all necessary entities for interview testing."""
    # Admin
    admin = User(
        email="admin@interview.test",
        role=UserRole.ADMIN,
        full_name="Test Admin",
        password_hash=get_password_hash("adminpass")
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    
    # Candidate
    candidate = User(
        email="candidate@interview.test",
        role=UserRole.CANDIDATE,
        full_name="Test Candidate",
        password_hash=get_password_hash("candpass")
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    
    # Paper
    paper = QuestionPaper(name="Interview Paper", admin_id=admin.id)
    session.add(paper)
    session.commit()
    session.refresh(paper)
    
    # Interview
    interview = InterviewSession(
        access_token="valid-test-token",
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.utcnow() - timedelta(minutes=5),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    return {"admin": admin, "candidate": candidate, "paper": paper, "interview": interview}

def test_access_interview_valid(client, test_setup):
    interview = test_setup["interview"]
    response = client.get(f"/api/interview/access/{interview.access_token}")
    
    assert response.status_code == 200
    assert response.json()["message"] == "START"

@pytest.mark.skip(reason="Requires ffmpeg/real audio processing - skip in CI")
def test_start_session(client, session, test_setup):
    """Test requires real audio processing. Skip in headless environments."""
    interview = test_setup["interview"]
    files = {"enrollment_audio": ("enroll.wav", b"fake_audio", "audio/wav")}
    response = client.post(f"/api/interview/start-session/{interview.id}", files=files)
    
    assert response.status_code == 200
    assert response.json()["status"] == "LIVE"
    
    session.refresh(interview)
    assert interview.status == InterviewStatus.LIVE

def test_submit_answer_text(client, session, test_setup):
    interview = test_setup["interview"]
    
    q = Questions(content="Test Question", response_type="text")
    session.add(q)
    session.commit()
    session.refresh(q)
    
    data = {
        "session_id": interview.id,
        "question_id": q.id,
        "answer_text": "This is a test answer"
    }
    
    response = client.post("/api/interview/submit-answer-text", data=data)
    assert response.status_code == 200

def test_submit_persistence_check(client, session, test_setup):
    interview = test_setup["interview"]
    
    q = Questions(content="Persistence Q", response_type="text")
    session.add(q)
    session.commit()
    session.refresh(q)
    
    data = {
        "session_id": interview.id,
        "question_id": q.id,
        "answer_text": "Real Persistence Answer"
    }
    
    client.post("/api/interview/submit-answer-text", data=data)
    
    from sqlmodel import select
    stmt = select(InterviewResponse).where(InterviewResponse.answer_text == "Real Persistence Answer")
    resp = session.exec(stmt).first()
    assert resp is not None
    assert resp.session_id == interview.id
