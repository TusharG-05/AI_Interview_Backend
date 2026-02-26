import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


def test_create_interview_session(session, test_users):
    admin, candidate = test_users

    from app.models.db_models import QuestionPaper, InterviewSession, InterviewStatus

    paper = QuestionPaper(name="Test Paper", adminUser=admin.id)
    session.add(paper)
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc) + timedelta(hours=1),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED
    )
    session.add(interview)
    session.commit()

    assert interview.id is not None
    assert interview.access_token is not None

def test_access_interview_invalid_token(client):
    response = client.get("/api/interview/access/invalid-token")
    assert response.status_code == 404
    assert "Invalid Interview Link" in response.json()["message"]

def test_access_interview_valid(session, client, test_users):
    admin, candidate = test_users

    from app.models.db_models import InterviewSession, QuestionPaper, InterviewStatus

    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc) - timedelta(minutes=10),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED
    )
    session.add(interview)
    session.commit()

    response = client.get(f"/api/interview/access/{interview.access_token}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["message"] == "START"
    assert data["interview_id"] == interview.id

def test_start_session(session, client, test_users):
    admin, candidate = test_users

    from app.models.db_models import InterviewSession, QuestionPaper, InterviewStatus

    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        duration_minutes=60,
        status=InterviewStatus.SCHEDULED
    )
    session.add(interview)
    session.commit()

    with patch("app.services.audio.AudioService.save_audio_blob") as mock_save:
        with patch("app.services.audio.AudioService.calculate_energy", return_value=100) as mock_energy:
             with patch("app.services.audio.AudioService.cleanup_audio") as mock_cleanup:
                files = {"enrollment_audio": ("enroll.wav", b"fake-audio-content", "audio/wav")}
                response = client.post(f"/api/interview/start-session/{interview.id}", files=files)

                assert response.status_code == 200
                assert response.json()["data"]["status"] == "LIVE"

                session.refresh(interview)
                assert interview.status == InterviewStatus.LIVE
                assert interview.start_time is not None

def test_submit_answer_text(session, client, test_users):
    admin, candidate = test_users

    from app.models.db_models import InterviewSession, QuestionPaper, Questions, InterviewStatus

    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()

    question = Questions(paper_id=paper.id, content="What is AI?")
    session.add(question)
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.LIVE
    )
    session.add(interview)
    session.commit()

    payload = {
        "interview_id": interview.id,
        "question_id": question.id,
        "answer_text": "AI is Artificial Intelligence."
    }
    response = client.post("/api/interview/submit-answer-text", data=payload)
    assert response.status_code == 200

    from app.models.db_models import Answers
    assert session.query(Answers).count() == 1
    saved_answer = session.query(Answers).first()
    assert saved_answer.candidate_answer == "AI is Artificial Intelligence."

def test_evaluate_answer_modal_fallback(session, client, test_users):
    admin, candidate = test_users

    from app.models.db_models import InterviewSession, QuestionPaper, Questions, InterviewStatus

    paper = QuestionPaper(name="Test Paper")
    session.add(paper)
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.LIVE
    )
    session.add(interview)
    session.commit()

    with patch("app.services.interview.evaluate_answer_content") as mock_eval:
        mock_eval.return_value = {"feedback": "Good job", "score": 8.5}

        payload = {
            "question": "What is AI?",
            "answer": "Artificial Intelligence"
        }
        response = client.post("/api/interview/evaluate-answer", json=payload)
        assert response.status_code == 200
        assert response.json()["data"]["score"] == 8.5
