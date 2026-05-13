from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..models.db_models import CandidateStatus, InterviewSession, InterviewStatus, QuestionAttempt, Questions, CodingQuestions
from sqlmodel import Session, select


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

    # For started sessions, enforce interview duration.
    if started:
        if session_obj.start_time is not None:
            # 1. GLOBAL TIMER MODE: Enforce strict duration from start_time.
            if session_obj.allow_question_navigate:
                start_time = to_utc(session_obj.start_time)
                duration_deadline = start_time + timedelta(minutes=session_obj.duration_minutes)
                if now_utc > duration_deadline:
                    return InterviewAccessDecision(
                        allowed=False,
                        reason="duration_expired",
                        duration_expired=True,
                    )
            # 2. SEQUENTIAL MODE: Relaxation.
            # Candidates get their full expected budget (sum of question times) 
            # plus a 1-hour wall-clock buffer for disconnections/breaks.
            else:
                # Calculate total expected duration based on budgets
                # Theory: 5m each, Coding: 20m each
                theory_count = 0
                if session_obj.paper:
                    try:
                        theory_count = session_obj.paper.question_count or 0
                    except Exception:
                        pass
                
                coding_count = 0
                if session_obj.coding_paper:
                    try:
                        coding_count = session_obj.coding_paper.question_count or 0
                    except Exception:
                        pass
                
                # Total budget in minutes
                total_budget_mins = (theory_count * 5) + (coding_count * 20)
                
                # Use max of calculated budget or duration_minutes (legacy support)
                base_duration = max(total_budget_mins, session_obj.duration_minutes or 0)
                
                # Safety limit = Total Duration + 60 minute buffer
                start_time = to_utc(session_obj.start_time)
                if now_utc > start_time + timedelta(minutes=base_duration + 60):
                    return InterviewAccessDecision(
                        allowed=False,
                        reason="duration_expired_safety",
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

def get_timer_sync_data(
    db: Session, 
    session_obj: InterviewSession, 
    question_id: int | None = None,
    coding_question_id: int | None = None
) -> dict:
    """
    Unified logic to calculate remaining time for both Global and Sequential modes.
    Logic moved from router to service for cleaner architecture.
    """
    now = datetime.now(timezone.utc)
    
    # 1. GLOBAL TIMER MODE (Navigation allowed)
    if session_obj.allow_question_navigate:
        duration_secs = (session_obj.duration_minutes or 60) * 60
        time_remaining = duration_secs
        is_expired = False

        if session_obj.status in (InterviewStatus.LIVE, InterviewStatus.DISCONNECTED) and session_obj.start_time:
            # Re-use to_utc helper from this module
            start_t = to_utc(session_obj.start_time)
            elapsed_secs = (now - start_t).total_seconds()
            time_remaining = max(0, int(duration_secs - elapsed_secs))
            is_expired = time_remaining <= 0
        
        return {
            "mode": "global",
            "time_remaining": time_remaining,
            "status": session_obj.status.value if hasattr(session_obj.status, 'value') else str(session_obj.status),
            "is_expired": is_expired
        }
    
    # 2. SEQUENTIAL TIMER MODE (Per-question timing)
    else:
        # Normalize: Treat 0 as None (frontend might send 0 for "none")
        q_id = question_id if (question_id and question_id > 0) else None
        c_q_id = coding_question_id if (coding_question_id and coding_question_id > 0) else None

        if not q_id and not c_q_id:
            # If no valid ID provided in sequential mode, return global status/time as fallback
            duration_secs = (session_obj.duration_minutes or 60) * 60
            return {
                "mode": "sequential",
                "time_remaining": int(duration_secs),
                "status": session_obj.status.value if hasattr(session_obj.status, 'value') else str(session_obj.status),
                "message": "valid_question_id_required"
            }

        # Check if an attempt already exists for this specific question (theory or coding)
        stmt = select(QuestionAttempt).where(QuestionAttempt.session_id == session_obj.id)
        if q_id:
            stmt = stmt.where(QuestionAttempt.question_id == q_id)
        else:
            stmt = stmt.where(QuestionAttempt.coding_question_id == c_q_id)
            
        attempt = db.exec(stmt).first()
        
        # Identify question type and default duration if first time
        if not attempt:
            q_type = "theory"
            duration = 300 # Default 5 mins
            
            if c_q_id:
                q_obj = db.get(CodingQuestions, c_q_id)
                if not q_obj:
                    return {"error": "Coding question not found", "status_code": 404}
                q_type = "coding"
                duration = 1200 # Default 20 mins for coding
            else:
                q_obj = db.get(Questions, q_id)
                if not q_obj:
                    return {"error": "Theory question not found", "status_code": 404}
                
                if q_obj.response_type == "code" or (q_obj.question_text and q_obj.question_text.startswith("__coding__")):
                    q_type = "coding"
                    duration = 1200 # Default 20 mins
            
            attempt = QuestionAttempt(
                session_id=session_obj.id,
                question_id=q_id,
                coding_question_id=c_q_id,
                question_type=q_type,
                start_time=now,
                duration_seconds=duration,
                status="active"
            )
            db.add(attempt)
            db.commit()
            db.refresh(attempt)
            
        # Calculate remaining time for the attempt
        start_t = to_utc(attempt.start_time)
        elapsed = (now - start_t).total_seconds()
        time_remaining = max(0, int(attempt.duration_seconds - elapsed))
        is_expired = time_remaining <= 0
        
        if is_expired and attempt.status == "active":
            attempt.status = "expired"
            attempt.expired_at = now
            db.add(attempt)
            db.commit()
            
        return {
            "mode": "sequential",
            "question_id": question_id,
            "coding_question_id": coding_question_id,
            "time_remaining": time_remaining,
            "status": attempt.status,
            "is_expired": is_expired
        }
