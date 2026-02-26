import pytest
import json
from datetime import datetime, timezone, timedelta
import app.models.db_models  # side-effect import registers tables

def test_print_admin_results_format(session, client):
    from app.models.db_models import User, UserRole, QuestionPaper, Questions, InterviewSession, InterviewResult, InterviewStatus, Answers
    from app.auth.security import get_password_hash, create_access_token
    
    # 1. Setup Admin
    admin = User(
        email="admin_format@test.com", 
        full_name="Admin Format", 
        password_hash=get_password_hash("test"), 
        role=UserRole.ADMIN
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    
    token = create_access_token(data={"sub": admin.email})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Setup Paper & Question
    paper = QuestionPaper(name="Format Paper", adminUser=admin.id)
    session.add(paper)
    session.commit()
    session.refresh(paper)
    
    q1 = Questions(
        paper_id=paper.id, 
        content="What is AI?", 
        question_text="Please define AI.", 
        topic="Technology", 
        difficulty="medium", 
        marks=10, 
        response_type="text"
    )
    session.add(q1)
    session.commit()
    
    # 3. Setup Candidate
    candidate = User(
        email="cand_format@test.com", 
        full_name="Candidate Format", 
        password_hash=get_password_hash("test"), 
        role=UserRole.CANDIDATE
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    
    # 4. Setup Interview Session
    interview = InterviewSession(
        admin_id=admin.id, 
        candidate_id=candidate.id, 
        paper_id=paper.id, 
        schedule_time=datetime.now(timezone.utc), 
        duration_minutes=60, 
        status=InterviewStatus.COMPLETED,
        is_completed=True
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    # 5. Setup Interview Result & Answer
    result = InterviewResult(interview_id=interview.id, total_score=9.5)
    session.add(result)
    session.commit()
    session.refresh(result)
    
    answer = Answers(
        interview_result_id=result.id, 
        question_id=q1.id, 
        candidate_answer="Artificial Intelligence.", 
        feedback="Correct definition.", 
        score=9.5
    )
    session.add(answer)
    session.commit()
    
    # 6. Fetch from API
    response = client.get(f"/api/admin/results/{interview.id}", headers=headers)
    
    print("\n\n--- ACTUAL JSON RESPONSE ---\n")
    print(json.dumps(response.json(), indent=2))
    print("\n----------------------------\n")
    
    assert response.status_code == 200
    
    # Simple assertions to verify top-level requested keys exist
    data = response.json()["data"]
    assert "interviewData" in data
    assert "Interview_response" in data
    assert len(data["Interview_response"]) > 0
    assert "question_id" in data["Interview_response"][0]
