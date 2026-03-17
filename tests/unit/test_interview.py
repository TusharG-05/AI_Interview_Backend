import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


def test_create_interview_session(session, test_users):
    admin, candidate, super_admin = test_users

    from app.models.db_models import QuestionPaper, InterviewSession, InterviewStatus

    paper = QuestionPaper(name="Test Paper", admin_user=admin.id)
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

def test_access_interview_invalid_token(client, auth_headers):
    response = client.get("/api/interview/access/invalid-token", headers=auth_headers)
    assert response.status_code == 404
    assert "Invalid Interview Link" in response.json()["message"]

def test_access_interview_valid(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users

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

    response = client.get(f"/api/interview/access/{interview.access_token}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    # Check that it returns the exact schema IDs (the message field was removed from schema)
    assert data["id"] == interview.id

def test_start_session(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users

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
                response = client.post(f"/api/interview/start-session/{interview.id}", files=files, headers=auth_headers)

                assert response.status_code == 200
                assert response.json()["data"]["status"] == "LIVE"

                session.refresh(interview)
                assert interview.status == InterviewStatus.LIVE
                assert interview.start_time is not None

def test_submit_answer_text(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users

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
    response = client.post("/api/interview/submit-answer-text", data=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["question"]["id"] == question.id

    from app.models.db_models import Answers
    assert session.query(Answers).count() == 1
    saved_answer = session.query(Answers).first()
    assert saved_answer.candidate_answer == "AI is Artificial Intelligence."

def test_evaluate_answer_modal_fallback(session, client, test_users, auth_headers):
    admin, candidate, super_admin = test_users

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
        response = client.post("/api/interview/evaluate-answer", json=payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["score"] == 8.5


def test_submit_answer_text_evaluates_immediately(session, client, test_users, auth_headers):
    """score and feedback should be present immediately in the API response,
    and InterviewResult.total_score / InterviewSession.total_score should be updated."""
    admin, candidate, super_admin = test_users

    from app.models.db_models import (
        InterviewSession, QuestionPaper, Questions, InterviewStatus, InterviewResult
    )

    paper = QuestionPaper(name="Eval Paper")
    session.add(paper)
    session.commit()

    question = Questions(paper_id=paper.id, content="Explain recursion.", question_text="Explain recursion.")
    session.add(question)
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.LIVE,
    )
    session.add(interview)
    session.commit()

    with patch("app.services.interview.evaluate_answer_content") as mock_eval:
        mock_eval.return_value = {"feedback": "Excellent", "score": 9.0}

        payload = {
            "interview_id": interview.id,
            "question_id": question.id,
            "answer_text": "Recursion is a function calling itself.",
        }
        response = client.post(
            "/api/interview/submit-answer-text", data=payload, headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()["data"]

    # Score and feedback must be in the response immediately
    assert data["score"] == 9.0, f"Expected score=9.0 in response, got {data['score']}"
    assert data["feedback"] == "Excellent"

    # InterviewResult.total_score must reflect the sum
    result_obj = session.exec(
        __import__("sqlmodel", fromlist=["select"]).select(InterviewResult).where(
            InterviewResult.interview_id == interview.id
        )
    ).first()
    assert result_obj is not None
    assert result_obj.total_score == 9.0, (
        f"InterviewResult.total_score should be 9.0, got {result_obj.total_score}"
    )

    # InterviewSession.total_score must also be updated
    session.refresh(interview)
    assert interview.total_score == 9.0, (
        f"InterviewSession.total_score should be 9.0, got {interview.total_score}"
    )


def test_two_answers_accumulate_total_score(session, client, test_users, auth_headers):
    """Submitting two answers should accumulate total_score as a sum."""
    admin, candidate, super_admin = test_users

    from app.models.db_models import (
        InterviewSession, QuestionPaper, Questions, InterviewStatus, InterviewResult
    )

    paper = QuestionPaper(name="Accumulation Paper")
    session.add(paper)
    session.commit()

    q1 = Questions(paper_id=paper.id, content="Q1?", question_text="Q1?")
    q2 = Questions(paper_id=paper.id, content="Q2?", question_text="Q2?")
    session.add_all([q1, q2])
    session.commit()

    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.LIVE,
    )
    session.add(interview)
    session.commit()

    scores = iter([
        {"feedback": "OK", "score": 5.0},
        {"feedback": "Great", "score": 3.0},
    ])

    with patch("app.services.interview.evaluate_answer_content", side_effect=scores):
        for q in [q1, q2]:
            client.post(
                "/api/interview/submit-answer-text",
                data={
                    "interview_id": interview.id,
                    "question_id": q.id,
                    "answer_text": f"Answer to {q.content}",
                },
                headers=auth_headers,
            )

    result_obj = session.exec(
        __import__("sqlmodel", fromlist=["select"]).select(InterviewResult).where(
            InterviewResult.interview_id == interview.id
        )
    ).first()
    assert result_obj is not None
    assert result_obj.total_score == 8.0, (
        f"Expected total_score=8.0 (5+3), got {result_obj.total_score}"
    )

    session.refresh(interview)
    assert interview.total_score == 8.0
