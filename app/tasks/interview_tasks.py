from ..core.celery_app import celery_app
from ..services.audio import AudioService
from ..services import interview as interview_service
from ..models.db_models import InterviewSession, InterviewResult, Answers, Questions, CandidateStatus, User
from ..services.email import EmailService
from ..core.database import engine
from ..core.logger import get_logger
from ..utils import format_iso_datetime, calculate_total_score, calculate_total_marks
from sqlmodel import Session, select
from datetime import datetime, timezone
import logging

logger = get_logger(__name__)
audio_service = AudioService()


def process_session_results(interview_id: int, db: Session = None):
    """
    Plain function: handles heavy AI processing (Whisper, LLM) after an interview finishes.
    Can be called directly (BackgroundTasks) or via Celery task wrapper.
    """
    close_db = False
    if db is None:
        db = Session(engine)
        close_db = True

    logger.info(f"--- PROCESSING SESSION {interview_id} ---")
    try:
        from sqlalchemy.orm import selectinload
        from ..models.db_models import QuestionPaper, CodingQuestionPaper
        session = db.exec(
            select(InterviewSession)
            .where(InterviewSession.id == interview_id)
            .options(
                selectinload(InterviewSession.paper),
                selectinload(InterviewSession.coding_paper),
            )
        ).first()
        if not session:
            logger.warning(f"Session {interview_id} not found for processing")
            return

        # Retrieve or create Result Object
        result_obj = db.exec(select(InterviewResult).where(InterviewResult.interview_id == interview_id)).first()
        if not result_obj:
            result_obj = InterviewResult(interview_id=interview_id)
            db.add(result_obj)
            db.commit()
            db.refresh(result_obj)

        # Fetch answers
        answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()
        logger.info(f"Session {interview_id}: processing {len(answers)} answer(s)")

        for resp in answers:
            # ── Audio transcription ──────────────────────────────────────
            if resp.audio_path and not (resp.candidate_answer or resp.transcribed_text):
                import asyncio
                loop = asyncio.new_event_loop()
                text = loop.run_until_complete(audio_service.speech_to_text(resp.audio_path))

                if session.enrollment_audio_path:
                    match, _ = loop.run_until_complete(audio_service.verify_speaker(session.enrollment_audio_path, resp.audio_path))
                    if not match:
                        text = f"[VOICE MISMATCH] {text}"

                resp.candidate_answer = text
                resp.transcribed_text = text
                loop.close()
                audio_service.cleanup_audio(resp.audio_path)

            # ── LLM Evaluation ───────────────────────────────────────────
            if resp.candidate_answer:
                # 1. If we already have feedback & score > 0 (e.g. from frontend pre-evaluation), skip LLM
                pre_evaluated = bool(resp.feedback) or (resp.score is not None and resp.score > 0)
                
                # Default empty score is 0.0 in schema, so we need to evaluate if it's 0.0 and no feedback provided
                needs_eval = not pre_evaluated

                if needs_eval:
                    from ..models.db_models import CodingQuestions
                    
                    q_text = "General Question"
                    resp_type = "text"
                    q_title = ""
                    q_marks = 10.0
                    
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
                    db.commit()
                else:
                    logger.info(f"  Answer {resp.id}: skipping evaluation (pre-evaluated: score={resp.score})")

        # ── Final Score Aggregation ──────────────────────────────────────
        db.refresh(result_obj)
        from ..models.db_models import CodingAnswers
        fresh_answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()
        fresh_coding_answers = db.exec(select(CodingAnswers).where(CodingAnswers.interview_result_id == result_obj.id)).all()
        
        all_scores = [r.score for r in fresh_answers if r.score is not None]
        all_scores += [r.score for r in fresh_coding_answers if r.score is not None]

        # Use sum (not average) to match the real-time score accumulated per answer
        computed_score = calculate_total_score(all_scores)
        result_obj.total_score = computed_score
        
        # Compute percentage against total marks from ALL assigned papers
        # (not just attempted questions) — fixes early-termination scoring bug
        total_marks = calculate_total_marks(session)
        percentage = (computed_score / total_marks * 100) if total_marks > 0 else 0.0
        
        # Auto-evaluate result_status based on 70% threshold
        if percentage >= 70.0:
            result_obj.result_status = "PASS"
        else:
            result_obj.result_status = "FAIL"
        
        logger.info(
            f"Session {interview_id}: obtained={computed_score}, "
            f"total_marks={total_marks}, percentage={percentage:.1f}%, "
            f"status={result_obj.result_status}"
        )
            
        session.total_score = computed_score
        
        db.add(result_obj)
        db.add(session)
        db.commit()
        logger.info(f"Session {interview_id} processing complete. Final score: {computed_score}, Status: {result_obj.result_status}")

        # ── Send Result Email to Candidate ──────────────────────────────
        try:
            admin_user = db.get(User, session.admin_id)
            admin_name = admin_user.full_name if admin_user else "Platform Admin"
            
            candidate_user = db.get(User, session.candidate_id)
            candidate_name = candidate_user.full_name if candidate_user else "Candidate"
            candidate_email = candidate_user.email if candidate_user else "tushar@chicmicstudios.in"

            # Format detailed result data for the template
            report_data = {
                "candidate_name": candidate_name,
                "date_str": format_iso_datetime(datetime.now(timezone.utc)),
                "id": str(session.id),
                "score": float(computed_score),
                "max_score": float(total_marks),
                "status": result_obj.result_status,
                "theory_count": len(fresh_answers),
                "coding_count": len(fresh_coding_answers),
                "admin_name": admin_name,
                "round_name": session.interview_round or "General Interview",
                "scheduled_time": format_iso_datetime(session.schedule_time),
                "start_time": format_iso_datetime(session.start_time) if session.start_time else "N/A",
                "duration_mins": str(session.duration_minutes),
                "proctoring_warnings": f"{session.tab_switch_count}/{session.tab_switch_limit}" if session.tab_switch_limit else "0"
            }
            
            email_service = EmailService()
            email_service.send_interview_result_email(candidate_email, report_data)
            logger.info(f"Result email dispatched to {candidate_email}")
        except Exception as email_err:
            logger.error(f"Failed to send result email for session {interview_id}: {email_err}")

    except Exception as e:
        logger.error(f"Session {interview_id} processing failed: {e}", exc_info=True)
        db.rollback()
    finally:
        if close_db:
            db.close()


@celery_app.task(name="app.tasks.interview_tasks.process_session_results_task")
def process_session_results_task(interview_id: int):
    """Celery wrapper — delegates to the plain function for testability and BackgroundTasks compatibility."""
    logger.info(f"--- CELERY TASK STARTING: Processing session {interview_id} ---")
    with Session(engine) as db:
        process_session_results(interview_id, db)


@celery_app.task(name="app.tasks.interview_tasks.expire_interviews_task")
def expire_interviews_task():
    """
    Periodic task to automatically mark expired interviews.
    Runs every minute to check for interviews that have passed their expiration time.
    """
    logger.info("--- CHECKING FOR EXPIRED INTERVIEWS ---")
    with Session(engine) as db:
        try:
            from ..models.db_models import InterviewStatus
            from datetime import timedelta
            
            now = datetime.now(timezone.utc)
            
            # Find interviews that are scheduled/live and have expired
            # We need to check expiration in Python since SQLModel doesn't support complex datetime arithmetic easily
            all_sessions = db.exec(
                select(InterviewSession).where(
                    InterviewSession.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.LIVE])
                )
            ).all()
            
            expired_sessions = []
            for session in all_sessions:
                schedule_time = session.schedule_time
                if schedule_time.tzinfo is None:
                    schedule_time = schedule_time.replace(tzinfo=timezone.utc)
                
                expiration_time = schedule_time + timedelta(minutes=session.duration_minutes)
                if now > expiration_time:
                    expired_sessions.append(session)
            
            expired_count = 0
            for session in expired_sessions:
                schedule_time = session.schedule_time
                if schedule_time.tzinfo is None:
                    schedule_time = schedule_time.replace(tzinfo=timezone.utc)
                
                expiration_time = schedule_time + timedelta(minutes=session.duration_minutes)
                
                if now > expiration_time:
                    logger.info(f"Expiring interview {session.id} (scheduled: {schedule_time}, duration: {session.duration_minutes}min)")
                    session.status = InterviewStatus.EXPIRED
                    db.add(session)
                    expired_count += 1
            
            if expired_count > 0:
                db.commit()
                logger.info(f"Marked {expired_count} interviews as expired")
            else:
                logger.debug("No interviews to expire")
                
        except Exception as e:
            logger.error(f"Error in expire_interviews_task: {e}", exc_info=True)
            db.rollback()


# Update the celery_app include to include the new task
from ..core.celery_app import celery_app  # Re-import to ensure it's updated
