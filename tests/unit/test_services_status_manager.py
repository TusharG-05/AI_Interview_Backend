
import pytest
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine
from app.models.db_models import InterviewSession, User, UserRole, CandidateStatus, StatusTimeline, ProctoringEvent
from app.services.status_manager import record_status_change, add_violation, check_and_suspend
from app.auth.security import get_password_hash

# --- Fixtures ---
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def interview_session(session):
    from app.models.db_models import QuestionPaper

    admin = User(email="admin@test.com", role=UserRole.ADMIN, password_hash="hash", full_name="Admin")
    candidate = User(email="cand@test.com", role=UserRole.CANDIDATE, password_hash="hash", full_name="Cand")
    session.add(admin)
    session.add(candidate)
    session.flush() # Ensure IDs are generated
    
    paper = QuestionPaper(name="Test Paper", adminUser=admin.id)
    session.add(paper)
    
    session.commit()
    session.refresh(paper)
    
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        access_token="abc",
        schedule_time=datetime.utcnow(),
        duration_minutes=30
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview

# --- Tests ---

def test_record_status_change(session, interview_session):
    # Test valid transition
    record_status_change(session, interview_session, CandidateStatus.LINK_ACCESSED)
    
    assert interview_session.current_status == CandidateStatus.LINK_ACCESSED
    
    # Check timeline
    timeline = session.query(StatusTimeline).filter_by(interview_id=interview_session.id).first()
    assert timeline is not None
    assert timeline.status == CandidateStatus.LINK_ACCESSED

def test_add_violation_warning(session, interview_session):
    # Add soft violation
    add_violation(session, interview_session, "gaze_away", "Looking left")
    
    session.refresh(interview_session)
    assert interview_session.warning_count == 1
    assert interview_session.is_suspended is False
    
    # Check event
    event = session.query(ProctoringEvent).filter_by(interview_id=interview_session.id).first()
    assert event.event_type == "gaze_away"
    assert event.severity == "warning"

def test_add_violation_critical(session, interview_session):
    # Add critical violation (multiple faces)
    add_violation(session, interview_session, "multiple_faces", "2 faces detected")
    
    session.refresh(interview_session)
    assert interview_session.is_suspended is True
    assert "Critical violation" in interview_session.suspension_reason
    assert interview_session.current_status == CandidateStatus.SUSPENDED

def test_max_warnings_suspension(session, interview_session):
    interview_session.max_warnings = 2
    session.add(interview_session)
    session.commit()
    
    # 1st warning
    add_violation(session, interview_session, "gaze_away")
    assert interview_session.is_suspended is False
    
    # 2nd warning -> Suspension
    add_violation(session, interview_session, "gaze_away")
    session.refresh(interview_session)
    
    assert interview_session.warning_count == 2
    assert interview_session.is_suspended is True
    assert "Exceeded maximum warnings" in interview_session.suspension_reason

def test_check_and_suspend_manual(session, interview_session):
    check_and_suspend(session, interview_session, "Manual check")
    
    session.refresh(interview_session)
    assert interview_session.is_suspended is True
    assert interview_session.suspension_reason == "Manual check"
    assert interview_session.current_status == CandidateStatus.SUSPENDED
