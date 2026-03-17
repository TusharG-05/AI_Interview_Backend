
import pytest
from app.models.db_models import InterviewStatus, InterviewSession, QuestionPaper, CodingQuestionPaper
from datetime import datetime, timezone, timedelta

def test_get_schedule_time_metadata(client, session, test_users):
    """
    Test that /schedule-time/{token} returns all requested metadata,
    and returns 200 OK with descriptive messages for all states.
    """
    admin, candidate, super_admin = test_users
    
    # 1. Setup Papers
    paper = QuestionPaper(
        name="Standard Paper", 
        description="Standard Description",
        admin_user=admin.id,
        question_count=5,
        total_marks=50
    )
    coding_paper = CodingQuestionPaper(
        name="Coding Paper", 
        description="Coding Description",
        admin_user=admin.id,
        question_count=2,
        total_marks=20
    )
    session.add(paper)
    session.add(coding_paper)
    session.commit()
    session.refresh(paper)
    session.refresh(coding_paper)
    
    # 2. Setup Interview Session (SCHEDULED, future)
    token_val = "test-metadata-token"
    schedule_time = datetime.now(timezone.utc) + timedelta(hours=5)
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        coding_paper_id=coding_paper.id,
        access_token=token_val,
        status=InterviewStatus.SCHEDULED,
        schedule_time=schedule_time,
        duration_minutes=120,
        max_questions=10
    )
    session.add(interview)
    session.commit()
    
    # 3. Test - SCHEDULED (Future)
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 200
    assert response.json()["message"] == "This interview is scheduled but has not started yet."
    data = response.json()["data"]
    assert data["duration_minutes"] == 120
    assert data["paper"]["name"] == "Standard Paper"
    assert data["coding_paper"]["name"] == "Coding Paper"

    # 4. Test - LIVE (Started)
    interview.status = InterviewStatus.LIVE
    interview.schedule_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    session.add(interview)
    session.commit()
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 200
    assert response.json()["message"] == "This interview is currently in progress (attempted)."
    assert response.json()["data"]["paper"] is not None # Rich data still present

    # 5. Test - COMPLETED
    interview.status = InterviewStatus.COMPLETED
    session.add(interview)
    session.commit()
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 200
    assert response.json()["message"] == "This interview has already been completed."

    # 6. Test - CANCELLED
    interview.status = InterviewStatus.CANCELLED
    session.add(interview)
    session.commit()
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 200
    assert response.json()["message"] == "This interview has been cancelled."

    # 7. Test - EXPIRED
    interview.status = InterviewStatus.SCHEDULED
    # Set schedule_time far in the past so it's expired based on duration
    interview.schedule_time = datetime.now(timezone.utc) - timedelta(hours=5)
    interview.duration_minutes = 60
    session.add(interview)
    session.commit()
    response = client.get(f"/api/interview/schedule-time/{token_val}")
    assert response.status_code == 200
    assert response.json()["message"] == "This interview link has expired."
