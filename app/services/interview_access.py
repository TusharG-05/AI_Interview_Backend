from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..models.db_models import CandidateStatus, InterviewSession, InterviewStatus


from ..core.config import LINK_VALIDITY_MINUTES


@dataclass
class InterviewAccessDecision:
    allowed: bool
    reason: str
    entry_window_expired: bool = False
    duration_expired: bool = False


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def has_been_accessed(session_obj: InterviewSession) -> bool:
    current_status = str(session_obj.current_status or "")
    return current_status not in ("", CandidateStatus.INVITED.value)


def has_started(session_obj: InterviewSession) -> bool:
    if session_obj.start_time is not None:
        return True

    if session_obj.status in (InterviewStatus.LIVE, InterviewStatus.COMPLETED):
        return True

    current_status = str(session_obj.current_status or "")
    started_statuses = {
        CandidateStatus.ENROLLMENT_STARTED.value,
        CandidateStatus.ENROLLMENT_COMPLETED.value,
        CandidateStatus.INTERVIEW_ACTIVE.value,
        CandidateStatus.INTERVIEW_COMPLETED.value,
        CandidateStatus.SUSPENDED.value,
    }
    return current_status in started_statuses


def evaluate_interview_access(session_obj: InterviewSession, now: datetime | None = None) -> InterviewAccessDecision:
    """
    Evaluate whether a candidate can access/start/continue an interview.

    Business rule:
    - Entry link is valid for the duration of the interview after scheduled time.
    - A session expires due to entry window only if it has not been accessed and has not started.
    - Ongoing/started sessions are governed by interview duration from start_time.
    """
    now_utc = to_utc(now or datetime.now(timezone.utc))

    if session_obj.status == InterviewStatus.CANCELLED:
        return InterviewAccessDecision(allowed=False, reason="cancelled")

    if session_obj.is_completed or session_obj.status == InterviewStatus.COMPLETED:
        return InterviewAccessDecision(allowed=False, reason="completed")

    schedule_time = to_utc(session_obj.schedule_time)

    started = has_started(session_obj)
    accessed = has_been_accessed(session_obj)

    # For started sessions, enforce interview duration from start_time.
    if started:
        if session_obj.start_time is not None:
            start_time = to_utc(session_obj.start_time)
            duration_deadline = start_time + timedelta(minutes=session_obj.duration_minutes)
            if now_utc > duration_deadline:
                return InterviewAccessDecision(
                    allowed=False,
                    reason="duration_expired",
                    duration_expired=True,
                )
        return InterviewAccessDecision(allowed=True, reason="started")

    entry_deadline = schedule_time + timedelta(minutes=session_obj.duration_minutes)
    should_expire_entry = now_utc > entry_deadline and (not accessed) and (not started)
    if should_expire_entry:
        return InterviewAccessDecision(
            allowed=False,
            reason="entry_window_expired",
            entry_window_expired=True,
        )

    if session_obj.status == InterviewStatus.EXPIRED:
        # Preserve explicit expired state for sessions that never started.
        return InterviewAccessDecision(allowed=False, reason="explicitly_expired")

    return InterviewAccessDecision(allowed=True, reason="entry_window_valid")