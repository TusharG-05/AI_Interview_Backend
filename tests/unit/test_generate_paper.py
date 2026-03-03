"""
Unit tests for POST /api/admin/generate-paper

Mocks the generate_questions_from_prompt service to avoid real LLM calls.
Uses the shared auth_headers fixture (admin user with JWT) from conftest.py.
"""

import pytest
from unittest.mock import patch


# --- Sample LLM output (3 questions) ---
MOCK_QUESTIONS = [
    {
        "question_text": "Explain how Python's GIL affects multi-threaded programs.",
        "topic": "Python",
        "difficulty": "Medium",
        "marks": 5,
        "response_type": "text",
    },
    {
        "question_text": "What is the difference between async/await and threading?",
        "topic": "Concurrency",
        "difficulty": "Medium",
        "marks": 5,
        "response_type": "text",
    },
    {
        "question_text": "Design a REST API for a simple task management application.",
        "topic": "System Design",
        "difficulty": "Hard",
        "marks": 8,
        "response_type": "text",
    },
]


def test_generate_paper_success(session, client, auth_headers):
    """
    Successful generation: mock returns 3 questions, assert full DB persistence.
    """
    payload = {
        "ai_prompt": "Python backend developer with FastAPI experience",
        "years_of_experience": 3,
        "num_questions": 3,
    }

    with patch(
        "app.services.interview.generate_questions_from_prompt",
        return_value=MOCK_QUESTIONS,
    ):
        response = client.post(
            "/api/admin/generate-paper",
            json=payload,
            headers=auth_headers,
        )

    assert response.status_code == 201, response.text
    data = response.json()["data"]

    # Paper level assertions
    assert data["question_count"] == 3
    assert data["total_marks"] == 18  # 5 + 5 + 8
    assert "AI Generated" in data["name"] or data["name"]  # has a name
    assert data["description"] != ""

    # Questions list assertions
    assert len(data["questions"]) == 3
    first_q = data["questions"][0]
    assert first_q["question_text"] == MOCK_QUESTIONS[0]["question_text"]
    assert first_q["topic"] == "Python"
    assert first_q["difficulty"] == "Medium"
    assert first_q["marks"] == 5
    assert first_q["response_type"] == "text"

    # Verify DB persistence
    from app.models.db_models import QuestionPaper, Questions
    paper = session.get(QuestionPaper, data["id"])
    assert paper is not None
    assert paper.question_count == 3
    saved_questions = session.query(Questions).filter(Questions.paper_id == paper.id).all()
    assert len(saved_questions) == 3


def test_generate_paper_custom_name(session, client, auth_headers):
    """
    Custom paper_name is respected.
    """
    payload = {
        "ai_prompt": "Django ORM and REST framework expert",
        "years_of_experience": 5,
        "num_questions": 2,
        "paper_name": "Django Expert Round",
    }

    with patch(
        "app.services.interview.generate_questions_from_prompt",
        return_value=MOCK_QUESTIONS[:2],
    ):
        response = client.post(
            "/api/admin/generate-paper",
            json=payload,
            headers=auth_headers,
        )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["name"] == "Django Expert Round"
    assert data["question_count"] == 2


def test_generate_paper_validation_num_questions_zero(client, auth_headers):
    """
    num_questions=0 must be rejected with 422.
    """
    payload = {
        "ai_prompt": "Python developer",
        "years_of_experience": 2,
        "num_questions": 0,
    }
    response = client.post(
        "/api/admin/generate-paper",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_generate_paper_validation_prompt_too_short(client, auth_headers):
    """
    ai_prompt shorter than 5 characters must be rejected with 422.
    """
    payload = {
        "ai_prompt": "Py",
        "years_of_experience": 2,
        "num_questions": 3,
    }
    response = client.post(
        "/api/admin/generate-paper",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_generate_paper_validation_negative_experience(client, auth_headers):
    """
    years_of_experience < 0 must be rejected with 422.
    """
    payload = {
        "ai_prompt": "Python backend developer",
        "years_of_experience": -1,
        "num_questions": 3,
    }
    response = client.post(
        "/api/admin/generate-paper",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_generate_paper_llm_failure(client, auth_headers):
    """
    If LLM raises ValueError the endpoint should return 503.
    """
    payload = {
        "ai_prompt": "Python backend developer",
        "years_of_experience": 3,
        "num_questions": 3,
    }

    with patch(
        "app.services.interview.generate_questions_from_prompt",
        side_effect=ValueError("LLM unreachable"),
    ):
        response = client.post(
            "/api/admin/generate-paper",
            json=payload,
            headers=auth_headers,
        )

    assert response.status_code == 503
    assert "AI service unavailable" in response.json().get("message", "")


def test_generate_paper_requires_admin(client, session):
    """
    Unauthenticated request should get 401.
    """
    payload = {
        "ai_prompt": "Python backend developer",
        "years_of_experience": 3,
        "num_questions": 3,
    }
    response = client.post("/api/admin/generate-paper", json=payload)
    assert response.status_code == 401
