from ..core.celery_app import celery_app
from ..services.audio import AudioService
from ..services import interview as interview_service
from ..models.db_models import InterviewSession, InterviewResult, Answers, Questions, CandidateStatus, User, CodingAnswers, CodingQuestions, InterviewStatus
from ..services.email import EmailService
from ..core.database import engine
from ..core.logger import get_logger
from ..core.config import LINK_VALIDITY_MINUTES
from ..utils import format_iso_datetime, calculate_total_score, calculate_total_marks
from sqlmodel import Session, select
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import selectinload
import asyncio

logger = get_logger(__name__)
audio_service = AudioService()


def _get_or_create_result_obj(db: Session, interview_id: int) -> InterviewResult:
    """Retrieve or create a result object for an interview session."""
    result_obj = db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
    if not result_obj:
        result_obj = InterviewResult(interview_id=interview_id)
        db.add(result_obj)
        db.commit()
        db.refresh(result_obj)
    return result_obj


def _process_answer_transcription(resp: Answers, session: InterviewSession):
    """Handle audio transcription and speaker verification if needed."""
    if not (resp.audio_path and not (resp.candidate_answer or resp.transcribed_text)):
        return

    loop = asyncio.new_event_loop()
    try:
        text = loop.run_until_complete(audio_service.speech_to_text(resp.audio_path))

        if session.enrollment_audio_path:
            match, _ = loop.run_until_complete(audio_service.verify_speaker(session.enrollment_audio_path, resp.audio_path))
            if not match:
                text = f"[VOICE MISMATCH] {text}"

        resp.candidate_answer = text
        resp.transcribed_text = text
        audio_service.cleanup_audio(resp.audio_path)
    finally:
        loop.close()


def _process_answer_evaluation(db: Session, resp: Answers):
    """Evaluate a single answer using LLM service."""
    if not resp.candidate_answer:
        return

    # Skip if already pre-evaluated
    if bool(resp.feedback) or (resp.score is not None and resp.score > 0):
        logger.info(f"  Answer {resp.id}: skipping evaluation (pre-evaluated)")
        return

    q_text, resp_type, q_title, q_marks = "General Question", "text", "", 10.0

    if resp.question_id:
        q = db.get(Questions, resp.question_id)
        if q:
            q_text = q.question_text or q.content or "General Question"
            resp_type = q.response_type
            q_title = q.question_text or q.content or ""
            q_marks = float(q.marks or 10.0)
    elif resp.coding_question_id:
        cq = db.get(CodingQuestions, resp.coding_question_id)
        if cq:
            q_text = cq.problem_statement or cq.title or "Coding Problem"
            resp_type = "code"
            q_title = cq.title or ""
            q_marks = float(cq.marks or 10.0)

    logger.info(f"  Answer {resp.id}: evaluating (type={resp_type}, marks={q_marks})...")
    evaluation = interview_service.evaluate_answer_content(
        q_text, resp.candidate_answer,
        response_type=resp_type or "text",
        question_title=q_title,
        question_marks=q_marks,
    )

    resp.feedback = evaluation.get("feedback", "")
    resp.score = evaluation.get("score")
    logger.info(f"  Answer {resp.id}: score={resp.score}")
    db.add(resp)


def _calculate_and_save_final_results(db: Session, session: InterviewSession, result_obj: InterviewResult):
    """Calculate totals, status, and save to DB."""
    db.refresh(result_obj)
    
    fresh_answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()
    fresh_coding_answers = db.exec(select(CodingAnswers).where(CodingAnswers.interview_result_id == result_obj.id)).all()
    
    all_scores = [r.score for r in fresh_answers if r.score is not None]
    all_scores += [r.score for r in fresh_coding_answers if r.score is not None]

    computed_score = calculate_total_score(all_scores)
    result_obj.total_score = computed_score
    
    total_marks = calculate_total_marks(session)
    percentage = (computed_score / total_marks * 100) if total_marks > 0 else 0.0
    
    result_obj.result_status = "PASS" if percentage >= 70.0 else "FAIL"
    session.total_score = computed_score
    
    db.add(result_obj)
    db.add(session)
    db.commit()
    
    logger.info(f"Session {session.id} processing complete. Score: {computed_score}, Status: {result_obj.result_status}")
    return computed_score, total_marks, fresh_answers, fresh_coding_answers


def _send_result_email(db: Session, session: InterviewSession, result_obj: InterviewResult, computed_score, total_marks, theory_count, coding_count):
    """Send summary email to the candidate."""
    try:
        admin_user = db.get(User, session.admin_id)
        admin_name = admin_user.full_name if admin_user else "Platform Admin"
        
        candidate_user = db.get(User, session.candidate_id)
        candidate_name = candidate_user.full_name if candidate_user else "Candidate"
        candidate_email = candidate_user.email if candidate_user else ""
        
        if not candidate_email:
            logger.warning(f"No email for candidate {session.candidate_id}, skipping result email.")
            return

        report_data = {
            "candidate_name": candidate_name,
            "date_str": format_iso_datetime(datetime.now(timezone.utc)),
            "id": str(session.id),
            "score": float(computed_score),
            "max_score": float(total_marks),
            "status": result_obj.result_status,
            "theory_count": theory_count,
            "coding_count": coding_count,
            "admin_name": admin_name,
            "round_name": session.interview_round or "General Interview",
            "scheduled_time": format_iso_datetime(session.schedule_time),
            "start_time": format_iso_datetime(session.start_time) if session.start_time else "N/A",
            "duration_mins": str(session.duration_minutes),
            "proctoring_warnings": f"{session.tab_switch_count}/{session.max_warnings}" if session.max_warnings else "0"
        }
        
        EmailService().send_interview_result_email(candidate_email, report_data)
        logger.info(f"Result email dispatched to {candidate_email}")
    except Exception as email_err:
        logger.error(f"Failed to send result email for session {session.id}: {email_err}")


def process_session_results(interview_id: int, db: Session = None):
    """
    Plain function: handles heavy AI processing (Whisper, LLM) after an interview finishes.
    """
    close_db = False
    if db is None:
        db = Session(engine)
        close_db = True

    logger.info(f"--- PROCESSING SESSION {interview_id} ---")
    try:
        session = db.exec(
            select(InterviewSession)
            .where(InterviewSession.id == interview_id)
            .options(selectinload(InterviewSession.paper), selectinload(InterviewSession.coding_paper))
        ).first()
        
        if not session:
            logger.warning(f"Session {interview_id} not found")
            return

        result_obj = _get_or_create_result_obj(db, interview_id)
        answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()

        for resp in answers:
            _process_answer_transcription(resp, session)
            _process_answer_evaluation(db, resp)
            db.commit()

        score, total, theory, coding = _calculate_and_save_final_results(db, session, result_obj)
        _send_result_email(db, session, result_obj, score, total, len(theory), len(coding))

    except Exception as e:
        logger.error(f"Session {interview_id} processing failed: {e}", exc_info=True)
        db.rollback()
    finally:
        if close_db:
            db.close()


@celery_app.task(name="app.tasks.interview_tasks.process_session_results_task")
def process_session_results_task(interview_id: int):
    """Celery wrapper."""
    process_session_results(interview_id)


def _expire_session(db: Session, session_obj: InterviewSession):
    """Helper to mark a single session as expired."""
    try:
        logger.info(f"Expiring session {session_obj.id} (Scheduled: {session_obj.schedule_time})")
        session_obj.status = InterviewStatus.EXPIRED
        session_obj.current_status = "Link Expired"
        db.add(session_obj)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to expire session {session_obj.id}: {e}")
        db.rollback()


@celery_app.task(name="app.tasks.interview_tasks.expire_interviews_task")
def expire_interviews_task():
    """
    Periodic task to mark active interviews as EXPIRED when they pass their
    respective validity window.
    """
    db = Session(engine)
    try:
        now = datetime.now(timezone.utc)
        # Find all active interviews that still need expiry checks
        stmt = select(InterviewSession).where(
            InterviewSession.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.LIVE])
        )
        scheduled_sessions = db.exec(stmt).all()
        
        expired_count = 0
        for s in scheduled_sessions:
            sched_time = s.schedule_time
            if sched_time.tzinfo is None:
                sched_time = sched_time.replace(tzinfo=timezone.utc)
            
            if s.status == InterviewStatus.SCHEDULED:
                expiration_limit = sched_time + timedelta(minutes=LINK_VALIDITY_MINUTES)
            else:
                start_time = s.start_time or sched_time
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                expiration_limit = start_time + timedelta(minutes=s.duration_minutes)
            
            if now > expiration_limit:
                _expire_session(db, s)
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cron: Expired {expired_count} interview sessions.")
            
    except Exception as e:
        logger.error(f"expire_interviews_task failed: {e}")
    finally:
        db.close()
