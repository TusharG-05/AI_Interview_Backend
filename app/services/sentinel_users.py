"""
Sentinel Users - System placeholder users for deleted accounts.

When an admin or candidate is deleted, their foreign keys in InterviewSession
are updated to point to these sentinel users instead of being set to NULL.
This allows admin_id and candidate_id to remain NOT NULL.

Sentinel emails:
  - __admin_deleted__@system  (role: admin)
  - __candidate_deleted__@system  (role: candidate)
"""

from typing import Optional, Tuple
from sqlmodel import Session, select
from ..models.db_models import User, UserRole

ADMIN_DELETED_EMAIL = "__admin_deleted__@system"
CANDIDATE_DELETED_EMAIL = "__candidate_deleted__@system"


def get_or_create_sentinel_users(session: Session) -> Tuple[User, User]:
    """
    Get or create the two sentinel placeholder users.
    Returns (admin_sentinel, candidate_sentinel).
    """
    admin_sentinel = session.exec(
        select(User).where(User.email == ADMIN_DELETED_EMAIL)
    ).first()

    if not admin_sentinel:
        admin_sentinel = User(
            email=ADMIN_DELETED_EMAIL,
            full_name="Deleted Admin",
            password_hash="__sentinel__",
            role=UserRole.ADMIN,
        )
        session.add(admin_sentinel)
        session.commit()
        session.refresh(admin_sentinel)

    candidate_sentinel = session.exec(
        select(User).where(User.email == CANDIDATE_DELETED_EMAIL)
    ).first()

    if not candidate_sentinel:
        candidate_sentinel = User(
            email=CANDIDATE_DELETED_EMAIL,
            full_name="Deleted Candidate",
            password_hash="__sentinel__",
            role=UserRole.CANDIDATE,
        )
        session.add(candidate_sentinel)
        session.commit()
        session.refresh(candidate_sentinel)

    return admin_sentinel, candidate_sentinel


def get_admin_sentinel_id(session: Session) -> int:
    """Get the ID of the admin sentinel user. Creates it if it doesn't exist."""
    sentinel, _ = get_or_create_sentinel_users(session)
    return sentinel.id


def get_candidate_sentinel_id(session: Session) -> int:
    """Get the ID of the candidate sentinel user. Creates it if it doesn't exist."""
    _, sentinel = get_or_create_sentinel_users(session)
    return sentinel.id


def is_sentinel_user(user: Optional[User]) -> bool:
    """Check if a User object is a sentinel/placeholder user."""
    if not user:
        return True
    return user.email in (ADMIN_DELETED_EMAIL, CANDIDATE_DELETED_EMAIL)
