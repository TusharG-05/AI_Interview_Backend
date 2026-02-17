import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

def test_full_interview_lifecycle(client, session, auth_headers):
    """
    Test the complete flow:
    1. Admin creates paper & session (simulated via DB)
    2. Candidate accesses link
    3. Candidate starts session (uploads enrollment)
    4. Candidate fetches next question
    5. Candidate submits answer (audio)
    6. Candidate finishes session
    """
    
    # --- 1. SETUP DATA ---
    from app.models.db_models import QuestionPaper, InterviewSession, InterviewStatus, Questions, CandidateStatus
    from app.auth.security import create_access_token
    
    # Create Paper
    paper = QuestionPaper(name="Integration Paper")
    session.add(paper)
    session.commit()
    
    # Create Question
    q1 = Questions(paper_id=paper.id, content="Intro Question", response_type="audio")
    session.add(q1)
    session.commit()
    
    # Create Session
    interview = InterviewSession(
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc) - timedelta(minutes=5),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED,
        current_status=CandidateStatus.INVITED
    )
    session.add(interview)
    session.commit()
    
    # --- 2. ACCESS LINK ---
    response = client.get(f"/api/interview/access/{interview.access_token}")
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "START"
    
    session.refresh(interview)
    assert interview.current_status == CandidateStatus.LINK_ACCESSED
    
    # --- 3. START SESSION ---
    # Mock Audio Service
    with patch("app.services.audio.AudioService.save_audio_blob"), \
         patch("app.services.audio.AudioService.calculate_energy", return_value=80), \
         patch("app.services.audio.AudioService.cleanup_audio"):
        
        files = {"enrollment_audio": ("enroll.wav", b"riff-wave-header...", "audio/wav")}
        response = client.post(f"/api/interview/start-session/{interview.id}", files=files)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "LIVE"
        
        session.refresh(interview)
        assert interview.status == InterviewStatus.LIVE
        assert interview.current_status == CandidateStatus.ENROLLMENT_COMPLETED
    
    # --- 4. GET NEXT QUESTION ---
    # Mock TTS for question reading
    with patch("app.services.audio.AudioService.text_to_speech"):
        response = client.get(f"/api/interview/next-question/{interview.id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["question_id"] == q1.id
        
        session.refresh(interview)
        assert interview.current_status == CandidateStatus.INTERVIEW_ACTIVE
        
    # --- 5. SUBMIT ANSWER ---
    with patch("app.services.audio.AudioService.save_audio_blob"):
        files = {
            "audio": ("answer.wav", b"answer-audio", "audio/wav")
        }
        data = {
            "interview_id": interview.id,
            "question_id": q1.id
        }
        response = client.post("/api/interview/submit-answer-audio", data=data, files=files)
        assert response.status_code == 200
        
        # Verify Answer Saved
        from app.models.db_models import Answers
        assert session.query(Answers).count() == 1
    
    # --- 6. FINISH SESSION ---
    with patch("app.routers.interview.process_session_results_unified") as mock_process:
        response = client.post(f"/api/interview/finish/{interview.id}")
        assert response.status_code == 200
        
        session.refresh(interview)
        assert interview.status == InterviewStatus.COMPLETED
        assert interview.is_completed is True
        assert interview.current_status == CandidateStatus.INTERVIEW_COMPLETED
        
        # Ensure background task was triggered
        mock_process.assert_called_once()
