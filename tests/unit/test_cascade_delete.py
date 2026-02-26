"""
Tests for cascade delete behavior and pre-deletion check endpoint.

Verifies:
1. DELETE /api/admin/users/{id} cascades to interview sessions
2. GET /api/admin/users/{id}/check-delete returns correct relationship info
"""
import app.models.db_models  # noqa: F401 — registers tables

import pytest
from datetime import datetime, timezone, timedelta


def _create_admin_and_get_token(session, client):
    """Helper: Create admin user + get JWT token."""
    from app.models.db_models import User, UserRole
    from app.auth.security import create_access_token, get_password_hash

    admin = User(
        email="admin_cascade@test.com",
        full_name="Admin Cascade",
        password_hash=get_password_hash("password"),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)

    token = create_access_token(data={"sub": admin.email})
    return admin, {"Authorization": f"Bearer {token}"}


def _create_candidate(session, email="candidate_cascade@test.com"):
    from app.models.db_models import User, UserRole
    from app.auth.security import get_password_hash

    candidate = User(
        email=email,
        full_name="Candidate Cascade",
        password_hash=get_password_hash("password"),
        role=UserRole.CANDIDATE,
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)
    return candidate


class TestCheckDeleteEndpoint:
    """Tests for GET /api/admin/users/{user_id}/check-delete"""

    def test_check_delete_clean_user(self, session, client):
        """User with no related data should return has_related_data=false."""
        admin, headers = _create_admin_and_get_token(session, client)
        candidate = _create_candidate(session)

        response = client.get(f"/api/admin/users/{candidate.id}/check-delete", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["has_related_data"] is False
        assert data["related_data"]["interviews_as_candidate"] == 0

    def test_check_delete_user_with_interviews(self, session, client):
        """User with interviews should return has_related_data=true."""
        from app.models.db_models import QuestionPaper, InterviewSession, InterviewStatus

        admin, headers = _create_admin_and_get_token(session, client)
        candidate = _create_candidate(session)

        paper = QuestionPaper(name="Check Paper", adminUser=admin.id)
        session.add(paper)
        session.commit()
        session.refresh(paper)

        interview = InterviewSession(
            admin_id=admin.id,
            candidate_id=candidate.id,
            paper_id=paper.id,
            schedule_time=datetime.now(timezone.utc),
            duration_minutes=60,
            status=InterviewStatus.SCHEDULED,
        )
        session.add(interview)
        session.commit()

        response = client.get(f"/api/admin/users/{candidate.id}/check-delete", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["has_related_data"] is True
        assert data["related_data"]["interviews_as_candidate"] == 1

    def test_check_delete_nonexistent_user(self, session, client):
        """Checking a nonexistent user should return 404."""
        admin, headers = _create_admin_and_get_token(session, client)

        response = client.get("/api/admin/users/99999/check-delete", headers=headers)
        assert response.status_code == 404


class TestCascadeDelete:
    """Tests for DELETE /api/admin/users/{user_id} with cascade behavior."""

    def test_delete_candidate_cascades_interviews(self, session, client):
        """Deleting a candidate should also delete their interview sessions."""
        from app.models.db_models import QuestionPaper, InterviewSession, InterviewStatus, InterviewResult

        admin, headers = _create_admin_and_get_token(session, client)
        candidate = _create_candidate(session)

        paper = QuestionPaper(name="Cascade Paper", adminUser=admin.id)
        session.add(paper)
        session.commit()
        session.refresh(paper)

        interview = InterviewSession(
            admin_id=admin.id,
            candidate_id=candidate.id,
            paper_id=paper.id,
            schedule_time=datetime.now(timezone.utc),
            duration_minutes=60,
            status=InterviewStatus.SCHEDULED,
        )
        session.add(interview)
        session.commit()
        session.refresh(interview)
        interview_id = interview.id

        # Delete the candidate
        response = client.delete(f"/api/admin/users/{candidate.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["interviews_deleted"] == 1

        # Verify interview is gone
        remaining = session.get(InterviewSession, interview_id)
        assert remaining is None

    def test_delete_clean_user(self, session, client):
        """Deleting a user with no related data should succeed cleanly."""
        admin, headers = _create_admin_and_get_token(session, client)
        candidate = _create_candidate(session)

        response = client.delete(f"/api/admin/users/{candidate.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["interviews_deleted"] == 0

    def test_cannot_delete_self(self, session, client):
        """Admin should not be able to delete their own account."""
        admin, headers = _create_admin_and_get_token(session, client)

        response = client.delete(f"/api/admin/users/{admin.id}", headers=headers)
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]
