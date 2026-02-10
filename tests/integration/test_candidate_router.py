
import pytest
from app.models.db_models import User, UserRole, InterviewSession, QuestionPaper
from app.auth.security import get_password_hash
from datetime import datetime, timedelta

@pytest.fixture
def candidate_setup(session):
    """Creates candidate user and related entities for testing."""
    # Admin (needed for paper creation)
    admin = User(
        email="admin@cand.test",
        role=UserRole.ADMIN,
        full_name="Admin",
        password_hash=get_password_hash("adminpass")
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    
    # Candidate
    candidate = User(
        email="candidate@test.com",
        role=UserRole.CANDIDATE,
        is_active=True,
        full_name="Candidate User",
        password_hash=get_password_hash("candpass")
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    
    return {"admin": admin, "candidate": candidate}

def test_upload_selfie_success(client, session, candidate_setup):
    from app.auth.dependencies import get_current_user
    from app.server import app
    
    candidate = candidate_setup["candidate"]
    app.dependency_overrides[get_current_user] = lambda: candidate
    
    files = {"file": ("selfie.jpg", b"fake_image_bytes", "image/jpeg")}
    
    response = client.post("/api/candidate/upload-selfie", files=files)
    
    assert response.status_code == 200
    assert response.json()["user_id"] == candidate.id
    
    session.refresh(candidate)
    assert candidate.profile_image_bytes is not None
    
    app.dependency_overrides.pop(get_current_user)

def test_get_history(client, session, candidate_setup):
    from app.auth.dependencies import get_current_user
    from app.server import app
    
    admin = candidate_setup["admin"]
    candidate = candidate_setup["candidate"]
    app.dependency_overrides[get_current_user] = lambda: candidate
    
    # Create paper
    paper = QuestionPaper(name="History Paper", admin_id=admin.id) 
    session.add(paper)
    session.commit()
    session.refresh(paper)

    # Create interview with all required FKs
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        access_token="history-token",
        schedule_time=datetime.utcnow() - timedelta(days=1),
        start_time=datetime.utcnow() - timedelta(days=1),
        total_score=85.0
    )
    session.add(interview)
    session.commit()
    
    response = client.get("/api/candidate/history")
    
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["score"] == 85.0
    
    app.dependency_overrides.pop(get_current_user)
