import pytest
from app.models.db_models import InterviewSession, InterviewStatus, CandidateStatus, InterviewRound
from app.routers.admin import _serialize_interview_admin_detail
from app.schemas.admin.results import GetInterviewResultResponse
from datetime import datetime, timezone

def test_serialize_interview_admin_detail_profile_image(session, test_users):
    """
    Test that _serialize_interview_admin_detail correctly serializes profile_image
    from the database and does NOT include profile_image_url.
    """
    admin, candidate, super_admin = test_users
    
    # 1. Update users with profile images
    admin.profile_image = "https://cloudinary.com/admin_avatar.jpg"
    candidate.profile_image = "https://cloudinary.com/candidate_selfie.jpg"
    session.add(admin)
    session.add(candidate)
    session.commit()
    
    # 2. Create an InterviewSession
    interview = InterviewSession(
        admin_id=admin.id,
        candidate_id=candidate.id,
        schedule_time=datetime.now(timezone.utc),
        status=InterviewStatus.SCHEDULED,
        current_status=CandidateStatus.INVITED,
        interview_round=InterviewRound.ROUND_1
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    
    # Eager load relationships for serialization
    from sqlalchemy.orm import selectinload
    from sqlmodel import select
    
    stmt = select(InterviewSession).where(InterviewSession.id == interview.id).options(
        selectinload(InterviewSession.admin),
        selectinload(InterviewSession.candidate),
        selectinload(InterviewSession.result),
        selectinload(InterviewSession.paper),
        selectinload(InterviewSession.coding_paper),
        selectinload(InterviewSession.proctoring_events)
    )
    interview_loaded = session.exec(stmt).first()
    
    # 3. Call serialization helper
    result = _serialize_interview_admin_detail(interview_loaded)
    
    # 4. Assertions
    assert isinstance(result, dict)
    
    # Check Admin
    assert result["admin_user"]["profile_image"] == "https://cloudinary.com/admin_avatar.jpg"
    assert "profile_image_url" not in result["admin_user"]
    
    # Check Candidate
    assert result["candidate_user"]["profile_image"] == "https://cloudinary.com/candidate_selfie.jpg"
    assert "profile_image_url" not in result["candidate_user"]

def test_admin_list_users_profile_image(client, session, test_users, auth_headers):
    """
    Test that GET /api/admin/users correctly returns profile_image and NO profile_image_url.
    """
    admin, candidate, super_admin = test_users
    candidate.profile_image = "candidate_image_path"
    session.add(candidate)
    session.commit()
    
    response = client.get("/api/admin/users", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()["data"]
    users = data["items"]
    # Find our candidate in the list
    cand_data = next((u for u in users if u["id"] == candidate.id), None)
    assert cand_data is not None
    assert cand_data["profile_image"] == "candidate_image_path"
    assert "profile_image_url" not in cand_data

def test_admin_get_user_detail_profile_image(client, session, test_users, auth_headers):
    """
    Test that GET /api/admin/users/{id} correctly returns profile_image and NO profile_image_url.
    """
    admin, candidate, super_admin = test_users
    candidate.profile_image = "detailed_image_path"
    session.add(candidate)
    session.commit()
    
    response = client.get(f"/api/admin/users/{candidate.id}", headers=auth_headers)
    assert response.status_code == 200
    
    cand_data = response.json()["data"]
    assert cand_data["profile_image"] == "detailed_image_path"
    assert "profile_image_url" not in cand_data
