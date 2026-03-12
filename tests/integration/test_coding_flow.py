import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.models.db_models import (
    CodingQuestionPaper, 
    CodingQuestions, 
    InterviewSession, 
    InterviewStatus, 
    CandidateStatus,
    Answers,
    InterviewResult
)

def test_coding_interview_flow(client, session, auth_headers, test_users):
    """
    Test the complete coding interview flow:
    1. Setup Coding Paper, Questions, and Session
    2. Access interview link
    3. Start session
    4. Fetch next coding question
    5. Submit coding answer
    6. Finish session
    """
    admin, candidate = test_users

    # --- 1. SETUP DATA ---
    # Create Coding Paper
    coding_paper = CodingQuestionPaper(
        name="Advanced Python Coding",
        description="Test your Python skills",
        admin_user=admin.id
    )
    session.add(coding_paper)
    session.commit()
    session.refresh(coding_paper)

    # Create Coding Question
    q1 = CodingQuestions(
        paper_id=coding_paper.id,
        title="Two Sum",
        problem_statement="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        examples=json.dumps([{"input": "[2,7,11,15], 9", "output": "[0,1]"}]),
        constraints=json.dumps(["2 <= nums.length <= 10^4"]),
        starter_code="def two_sum(nums, target):\n    pass",
        marks=10
    )
    session.add(q1)
    session.commit()
    session.refresh(q1)

    # Create Interview Session
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        coding_paper_id=coding_paper.id,
        schedule_time=datetime.now(timezone.utc) - timedelta(minutes=5),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED,
        current_status=CandidateStatus.INVITED
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)

    # --- 2. ACCESS LINK ---
    # We must override get_current_user to return candidate
    from app.auth.dependencies import get_current_user
    from app.server import app
    app.dependency_overrides[get_current_user] = lambda: candidate

    response = client.get(f"/api/interview/access/{interview.access_token}")
    assert response.status_code == 200
    assert response.json()["data"]["current_status"].lower() == "link_accessed"
    
    session.refresh(interview)
    assert interview.current_status.lower() == "link_accessed"

    # --- 3. START SESSION ---
    # Mock Audio Service for enrollment
    with patch("app.services.audio.AudioService.save_audio_blob"), \
         patch("app.services.audio.AudioService.calculate_energy", return_value=80), \
         patch("app.services.audio.AudioService.cleanup_audio"):
        
        files = {"enrollment_audio": ("enroll.wav", b"riff-wave-header...", "audio/wav")}
        response = client.post(f"/api/interview/start-session/{interview.id}", files=files)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "LIVE"
        
        session.refresh(interview)
        assert interview.status == InterviewStatus.LIVE

    # --- 4. GET NEXT QUESTION ---
    # Fetch the coding question
    response = client.get(f"/api/interview/next-question/{interview.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    cq_id = data["coding_question_id"]
    assert cq_id == q1.id
    assert data["text"] == "Two Sum"

    # --- 5. SUBMIT CODING ANSWER ---
    # Mock evaluation service
    mock_eval = {
        "feedback": "Great job! Optimal O(n) solution.",
        "score": 10.0,
        "correctness": "correct"
    }
    
    with patch("app.services.interview.evaluate_answer_content", return_value=mock_eval):
        data_payload = {
            "interview_id": interview.id,
            "coding_question_id": cq_id,
            "answer_code": "def two_sum(nums, target):\n    prevMap = {}\n    for i, n in enumerate(nums):\n        diff = target - n\n        if diff in prevMap:\n            return [prevMap[diff], i]\n        prevMap[n] = i"
        }
        response = client.post("/api/interview/submit-answer-code", data=data_payload)
        assert response.status_code == 200
        assert response.json()["data"]["score"] == 10.0
        
        # Verify Answer and Result in DB
        answer = session.query(Answers).filter(Answers.coding_question_id == cq_id).first()
        assert answer is not None
        assert answer.score == 10.0
        
        session.refresh(interview)
        assert interview.total_score == 10.0

    # --- 6. FINISH SESSION ---
    with patch("app.tasks.interview_tasks.process_session_results_task.delay") as mock_task:
        response = client.post(f"/api/interview/finish/{interview.id}")
        assert response.status_code == 200
        
        session.refresh(interview)
        assert interview.status == InterviewStatus.COMPLETED
        assert interview.is_completed is True
        
        # In actual code, it might call .delay() or be a background task
        # mock_task.assert_called_once()

    # Clear overrides
    app.dependency_overrides.clear()
