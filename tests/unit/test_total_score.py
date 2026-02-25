"""
Tests for total_score field in InterviewResultDetail and InterviewResultBrief.

Verifies:
1. GET /api/admin/results/{interview_id} → total_score in InterviewResultDetail
2. GET /api/admin/users/results         → total_score in InterviewResultBrief
"""
# IMPORTANT: Import all models at module level so SQLModel.metadata.create_all()
# in the session fixture registers every table, even when this file runs first.
import app.models.db_models  # noqa: F401 — side-effect import registers tables

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch


def _create_admin_and_get_token(session, client):
    """Helper: Create admin user + get JWT token."""
    from app.models.db_models import User, UserRole
    from app.auth.security import create_access_token, get_password_hash

    admin = User(
        email="admin_score@test.com",
        full_name="Admin Score",
        password_hash=get_password_hash("password"),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)

    token = create_access_token(data={"sub": admin.email})
    return admin, {"Authorization": f"Bearer {token}"}


def _create_completed_interview(session, admin, score: float):
    """Helper: Create a completed InterviewSession + InterviewResult with a given total_score."""
    from app.models.db_models import (
        User, UserRole, QuestionPaper, Questions, InterviewSession,
        InterviewResult, InterviewStatus
    )
    from app.auth.security import get_password_hash

    # Candidate
    candidate = User(
        email="candidate_score@test.com",
        full_name="Candidate Score",
        password_hash=get_password_hash("password"),
        role=UserRole.CANDIDATE,
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    # Paper + Question
    paper = QuestionPaper(name="Score Test Paper", admin_id=admin.id)
    session.add(paper)
    session.commit()
    session.refresh(paper)

    question = Questions(paper_id=paper.id, content="What is ML?")
    session.add(question)
    session.commit()

    # Interview Session
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        paper_id=paper.id,
        schedule_time=datetime.now(timezone.utc) - timedelta(hours=2),
        duration_minutes=60,
        status=InterviewStatus.COMPLETED,
        is_completed=True,
        total_score=score,  # Session-level score (redundant copy)
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)

    # InterviewResult — the authoritative source of total_score
    result = InterviewResult(
        interview_id=interview.id,
        total_score=score,
    )
    session.add(result)
    session.commit()
    session.refresh(result)

    return interview, result


class TestTotalScoreInResultDetail:
    """Tests for GET /api/admin/results/{interview_id}"""

    def test_total_score_returned_correctly(self, session, client):
        """total_score should match what was stored in InterviewResult."""
        admin, headers = _create_admin_and_get_token(session, client)
        interview, result = _create_completed_interview(session, admin, score=7.5)

        response = client.get(f"/api/admin/results/{interview.id}", headers=headers)
        assert response.status_code == 200, response.text

        data = response.json()["data"]
        assert data["total_score"] == 7.5, (
            f"Expected total_score=7.5 in InterviewResultDetail, got {data['total_score']}"
        )

    def test_total_score_none_when_not_processed(self, session, client):
        """total_score in InterviewResult defaults to None when unprocessed."""
        from app.models.db_models import (
            User, UserRole, QuestionPaper, InterviewSession,
            InterviewResult, InterviewStatus
        )
        from app.auth.security import get_password_hash, create_access_token

        admin = User(
            email="admin_none@test.com",
            full_name="Admin None",
            password_hash=get_password_hash("password"),
            role=UserRole.ADMIN,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        token = create_access_token(data={"sub": admin.email})
        headers = {"Authorization": f"Bearer {token}"}

        from app.services.sentinel_users import get_candidate_sentinel_id
        candidate_sentinel_id = get_candidate_sentinel_id(session)

        paper = QuestionPaper(name="No Score Paper", adminUser=admin.id)
        session.add(paper)
        session.commit()
        session.refresh(paper)

        interview = InterviewSession(
            admin_id=admin.id,
            candidate_id=candidate_sentinel_id,
            paper_id=paper.id,
            schedule_time=datetime.now(timezone.utc) - timedelta(hours=1),
            duration_minutes=60,
            status=InterviewStatus.COMPLETED,
            is_completed=True,
        )
        session.add(interview)
        session.commit()
        session.refresh(interview)

        # InterviewResult with default total_score (0.0)
        result = InterviewResult(interview_id=interview.id)
        session.add(result)
        session.commit()

        response = client.get(f"/api/admin/results/{interview.id}", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        # Default is 0.0 per db model
        assert data["total_score"] == 0.0, (
            f"Expected total_score=0.0 (default), got {data['total_score']}"
        )

    def test_total_score_in_nested_interview_object(self, session, client):
        """The nested 'interview.total_score' should reflect the InterviewSession-level score."""
        admin, headers = _create_admin_and_get_token(session, client)
        # We re-run in a fresh session scope so we need unique emails
        from app.models.db_models import User, UserRole, QuestionPaper, InterviewSession, InterviewResult, InterviewStatus
        from app.auth.security import get_password_hash, create_access_token

        # Use a second unique admin to avoid email conflict
        admin2 = User(
            email="admin_nested@test.com",
            full_name="Admin Nested",
            password_hash=get_password_hash("password"),
            role=UserRole.ADMIN,
        )
        session.add(admin2)
        session.commit()
        session.refresh(admin2)
        token2 = create_access_token(data={"sub": admin2.email})
        headers2 = {"Authorization": f"Bearer {token2}"}

        paper = QuestionPaper(name="Nested Score Paper", adminUser=admin2.id)
        session.add(paper)
        session.commit()
        session.refresh(paper)

        from app.services.sentinel_users import get_candidate_sentinel_id
        candidate_sentinel_id2 = get_candidate_sentinel_id(session)

        interview = InterviewSession(
            admin_id=admin2.id,
            candidate_id=candidate_sentinel_id2,
            paper_id=paper.id,
            schedule_time=datetime.now(timezone.utc) - timedelta(hours=1),
            duration_minutes=60,
            status=InterviewStatus.COMPLETED,
            is_completed=True,
            total_score=6.0,  # Session-level score
        )
        session.add(interview)
        session.commit()
        session.refresh(interview)

        result = InterviewResult(interview_id=interview.id, total_score=6.0)
        session.add(result)
        session.commit()

        response = client.get(f"/api/admin/results/{interview.id}", headers=headers2)
        assert response.status_code == 200, response.text
        data = response.json()["data"]

        # Verify both top-level and nested total_score
        assert data["total_score"] == 6.0
        assert data["interview"]["total_score"] == 6.0, (
            f"Nested interview.total_score should be 6.0, got {data['interview']['total_score']}"
        )


class TestTotalScoreInResultBrief:
    """Tests for GET /api/admin/users/results"""

    def test_total_score_in_brief_list(self, session, client):
        """total_score should appear correctly in the brief list endpoint."""
        admin, headers = _create_admin_and_get_token(session, client)
        interview, result = _create_completed_interview(session, admin, score=8.0)

        response = client.get("/api/admin/users/results", headers=headers)
        assert response.status_code == 200, response.text

        items = response.json()["data"]
        assert len(items) >= 1

        matching = [item for item in items if item["id"] == result.id]
        assert len(matching) == 1, "Expected our result to appear in the list"

        assert matching[0]["total_score"] == 8.0, (
            f"Expected total_score=8.0 in InterviewResultBrief, got {matching[0]['total_score']}"
        )

    def test_zero_score_not_filtered_out(self, session, client):
        """Ensure interviews with total_score=0.0 are still returned (not treated as falsy)."""
        admin, headers = _create_admin_and_get_token(session, client)
        interview, result = _create_completed_interview(session, admin, score=0.0)

        response = client.get("/api/admin/users/results", headers=headers)
        assert response.status_code == 200, response.text

        items = response.json()["data"]
        matching = [item for item in items if item["id"] == result.id]
        assert len(matching) == 1, "Result with score 0.0 should still appear"
        assert matching[0]["total_score"] == 0.0
