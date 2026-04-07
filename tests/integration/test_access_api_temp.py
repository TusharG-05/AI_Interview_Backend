import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.db_models import InterviewSession, User, UserRole, QuestionPaper, Questions, CodingQuestionPaper, CodingQuestions, InterviewStatus

def test_access_api_response(client: TestClient, session: Session, test_users):
    admin, candidate, _ = test_users
    
    # Create Paper
    paper = QuestionPaper(name="Access Test Paper", admin_user=admin.id)
    session.add(paper)
    session.commit()
    session.refresh(paper)
    
    q1 = Questions(id=1999, paper_id=paper.id, content="Q1", question_text="Q1", marks=5)
    session.add(q1)
    
    # Create Coding Paper
    cpaper = CodingQuestionPaper(name="Access Test Coding Paper", admin_user=admin.id)
    session.add(cpaper)
    session.commit()
    session.refresh(cpaper)
    
    cq1 = CodingQuestions(id=1888, paper_id=cpaper.id, title="CQ1", problem_statement="CQ1", marks=10)
    session.add(cq1)
    
    # Create Session
    token = "test_access_token_456"
    session_obj = InterviewSession(
        access_token=token,
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        coding_paper_id=cpaper.id,
        schedule_time=datetime.now(timezone.utc),
        duration_minutes=60,
        max_questions=10,
        status=InterviewStatus.LIVE
    )
    session.add(session_obj)
    session.commit()
    session.refresh(session_obj)
    
    # Dependency Override for Auth
    from app.auth.dependencies import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = lambda: candidate
    
    response = client.get(f"/api/interview/access/{token}")
    
    # Clean up override
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()["data"]
    print("\nAPI Response:")
    print(json.dumps(data, indent=2))
