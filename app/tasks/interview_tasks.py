from ..core.celery_app import celery_app
from ..services.audio import AudioService
from ..services import interview as interview_service
from ..models.db_models import InterviewSession, InterviewResult, Answers, Questions, CandidateStatus, User, CodingAnswers, CodingQuestions, InterviewStatus
from ..services.email import EmailService
from ..services.interview_access import evaluate_interview_access
from ..services.firebase import FirebaseNotificationService
from ..core.database import engine
from ..core.logger import get_logger
from ..core.config import LINK_VALIDITY_MINUTES, FRONTEND_URL
from ..services.status_manager import complete_interview_session
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
            q_marks = float(q.marks if q.marks is not None else 10.0)
    elif resp.coding_question_id:
        cq = db.get(CodingQuestions, resp.coding_question_id)
        if cq:
            q_text = cq.problem_statement or cq.title or "Coding Problem"
            resp_type = "code"
            q_title = cq.title or ""
            q_marks = float(cq.marks if cq.marks is not None else 10.0)

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
    
    logger.info(f"Session {session.id}: Found {len(fresh_answers)} theory answers and {len(fresh_coding_answers)} coding answers.")

    all_scores = [r.score for r in fresh_answers if r.score is not None]
    all_scores += [r.score for r in fresh_coding_answers if r.score is not None]

    computed_score = calculate_total_score(all_scores)
    result_obj.total_score = computed_score
    
    total_marks = calculate_total_marks(session)
    percentage = (computed_score / total_marks * 100) if total_marks > 0 else 0.0
    
    # Update status from intermediate states to terminal states
    if result_obj.result_status in ["PENDING", "PROCESSING", "COMPLETED"]:
        result_obj.result_status = "PASS" if percentage >= 70.0 else "FAIL"
    
    session.total_score = computed_score
    
    db.add(result_obj)
    db.add(session)
    db.commit()
    
    logger.info(f"Session {session.id} processing complete. Score: {computed_score}, Status: {result_obj.result_status}")
    return computed_score, total_marks, fresh_answers, fresh_coding_answers


def send_result_email_util(db: Session, session: InterviewSession, result_obj: InterviewResult, computed_score, total_marks, theory_count, coding_count):
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

        # Format scheduled time in India Standard Time for candidate-facing emails
        try:
            from zoneinfo import ZoneInfo
            ist = ZoneInfo("Asia/Kolkata")
        except Exception:
            ist = None

        sched = session.schedule_time
        if sched is not None:
            if sched.tzinfo is None:
                sched = sched.replace(tzinfo=timezone.utc)
            if ist:
                scheduled_time_str = sched.astimezone(ist).strftime("%Y-%m-%d %H:%M:%S %Z")
            else:
                scheduled_time_str = format_iso_datetime(sched)
        else:
            scheduled_time_str = ""

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
            "scheduled_time": scheduled_time_str,
            "start_time": format_iso_datetime(session.start_time) if session.start_time else "N/A",
            "duration_mins": str(session.duration_minutes),
            "proctoring_warnings": f"{session.tab_switch_count}/{session.max_warnings}" if session.max_warnings else "0"
        }
        
        EmailService().send_interview_result_email(candidate_email, report_data)
        logger.info(f"Result email dispatched to {candidate_email}")
    except Exception as email_err:
        logger.error(f"Failed to send result email for session {session.id}: {email_err}")


def send_result_push_notification(db: Session, session: InterviewSession):
    """
    Sends a Firebase push notification to the admin when an interview result is ready.
    Notification format:
      Title: "Interview is completed for candidate <candidate-name>."
      Body:  "Your result is calculated successfully.\nclick to view result - <FRONTEND_URL>/result/{interview_id}"
    """
    try:
        # Fetch the admin who owns this interview session
        admin_user = db.get(User, session.admin_id)
        if not admin_user:
            logger.warning(f"No admin found for session {session.id}, skipping push notification.")
            return

        admin_fcm_token = admin_user.fcm_token
        if not admin_fcm_token:
            logger.info(
                f"Admin (id={session.admin_id}) has no FCM token stored. "
                "Push notification skipped."
            )
            return

        # Resolve candidate name
        candidate_user = db.get(User, session.candidate_id)
        candidate_name = candidate_user.full_name if candidate_user else "Candidate"

        # Build notification payload
        result_url = f"{FRONTEND_URL.rstrip('/')}/result/{session.id}"
        title = f"{candidate_name}'s interview completed"
        body = "Your result is calculated successfully."
        data = {
            "screen": "result",
            "interview_id": str(session.id),
            "result_url": result_url,
        }

        success = FirebaseNotificationService.send_push_notification(
            token=admin_fcm_token,
            title=title,
            body=body,
            data=data,
        )
        
        
        if success:
            logger.info(
                f"Push notification sent to admin (id={session.admin_id}) "
                f"for completed interview {session.id}."
            )
        else:
            logger.warning(
                f"Push notification failed for admin (id={session.admin_id}), "
                f"interview {session.id}."
            )
    except Exception as notif_err:
        logger.error(
            f"Failed to send push notification for session {session.id}: {notif_err}"
        )


def process_session_results(interview_id: int, db: Session = None):
    """
    Synchronous fallback or direct invocation wrapper for testing.
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

        _calculate_and_save_final_results(db, session, result_obj)
        send_result_push_notification(db, session)

    except Exception as e:
        logger.error(f"Session {interview_id} processing failed: {e}", exc_info=True)
        db.rollback()
    finally:
        if close_db:
            db.close()

@celery_app.task(name="app.tasks.interview_tasks.process_single_answer_task")
def process_single_answer_task(answer_id: int, interview_id: int):
    """Process a single answer. Runs asynchronously in parallel."""
    with Session(engine) as db:
        resp = db.get(Answers, answer_id)
        if not resp:
            return
        session_obj = db.get(InterviewSession, interview_id)
        _process_answer_transcription(resp, session_obj)
        _process_answer_evaluation(db, resp)
        db.commit()
    return answer_id

@celery_app.task(name="app.tasks.interview_tasks.finalize_session_results_task")
def finalize_session_results_task(results, interview_id: int):
    """Callback after all answers are processed."""
    logger.info(f"--- FINALIZING SESSION {interview_id} ---")
    with Session(engine) as db:
        session_obj = db.exec(
            select(InterviewSession)
            .where(InterviewSession.id == interview_id)
            .options(selectinload(InterviewSession.paper), selectinload(InterviewSession.coding_paper))
        ).first()
        
        if not session_obj:
            return
            
        result_obj = _get_or_create_result_obj(db, interview_id)
        _calculate_and_save_final_results(db, session_obj, result_obj)
        send_result_push_notification(db, session_obj)

@celery_app.task(name="app.tasks.interview_tasks.process_session_results_task")
def process_session_results_task(interview_id: int):
    """Celery wrapper utilizing Chords for parallel processing, or synchronous loop if Celery is disabled."""
    from celery import chord
    import os
    from ..core.config import IS_ORCHESTRATOR
    
    use_celery = not IS_ORCHESTRATOR and os.getenv("DISABLE_CELERY", "false").lower() == "false"
    
    with Session(engine) as db:
        result_obj = _get_or_create_result_obj(db, interview_id)
        answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()
        answer_ids = [a.id for a in answers]
        
    if not answer_ids:
        if use_celery:
            finalize_session_results_task.delay([], interview_id)
        else:
            finalize_session_results_task([], interview_id)
        return
        
    if use_celery:
        logger.info(f"Spawning {len(answer_ids)} parallel evaluation tasks for Session {interview_id}")
        tasks = [process_single_answer_task.s(aid, interview_id) for aid in answer_ids]
        chord(tasks)(finalize_session_results_task.s(interview_id))
    else:
        logger.info(f"Celery disabled: Executing {len(answer_ids)} evaluation tasks synchronously for Session {interview_id}")
        results = []
        for aid in answer_ids:
            res = process_single_answer_task(aid, interview_id)
            results.append(res)
        finalize_session_results_task(results, interview_id)


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
    Periodic task to mark interviews as EXPIRED (if entry window missed) or
    COMPLETED (if duration limit reached).
    """
    db = Session(engine)
    try:
        now = datetime.now(timezone.utc)
        # Find all active interviews that still need expiry checks
        stmt = select(InterviewSession).where(
            InterviewSession.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.CONNECTED, InterviewStatus.LIVE, InterviewStatus.DISCONNECTED])
        )
        scheduled_sessions = db.exec(stmt).all()
        
        expired_count = 0
        for s in scheduled_sessions:
            access_decision = evaluate_interview_access(s, now=now)
            
            if access_decision.entry_window_expired:
                # Entry window (30 mins) passed without starting
                _expire_session(db, s)
                expired_count += 1
            
            elif access_decision.duration_expired:
                # Interview duration passed for a LIVE session
                if s.status in [InterviewStatus.LIVE, InterviewStatus.DISCONNECTED]:
                    complete_interview_session(
                        session=db,
                        interview_session=s,
                        reason="duration_timeout",
                        current_status_label="Completed (Time Limit)",
                    )
                    from ..core.tasks import run_background_task
                    run_background_task(process_session_results_task, s.id)
                    expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cron: Expired {expired_count} interview sessions.")
            
    except Exception as e:
        logger.error(f"expire_interviews_task failed: {e}")
    finally:
        db.close()
