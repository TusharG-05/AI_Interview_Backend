from ..core.celery_app import celery_app
from ..services.audio import AudioService
from ..services import interview as interview_service
from ..models.db_models import InterviewSession, InterviewResult, Answers, Questions, CandidateStatus
from ..core.database import engine
from ..core.logger import get_logger
from ..utils import format_iso_datetime, calculate_average_score
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
        session = db.get(InterviewSession, interview_id)
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
                    q = db.get(Questions, resp.question_id)
                    q_text = q.question_text or q.content or "General Question"

                    logger.info(f"  Answer {resp.id}: evaluating...")
                    evaluation = interview_service.evaluate_answer_content(q_text, resp.candidate_answer)

                    resp.feedback = evaluation.get("feedback", "")
                    resp.score = evaluation.get("score")

                    logger.info(f"  Answer {resp.id}: score={resp.score}")
                    db.add(resp)
                    db.commit()
                else:
                    logger.info(f"  Answer {resp.id}: skipping evaluation (pre-evaluated: score={resp.score})")

        # ── Final Score Aggregation ──────────────────────────────────────
        db.refresh(result_obj)
        fresh_answers = db.exec(select(Answers).where(Answers.interview_result_id == result_obj.id)).all()
        all_scores = [r.score for r in fresh_answers if r.score is not None]

        computed_score = calculate_average_score(all_scores)
        result_obj.total_score = computed_score
        session.total_score = computed_score
        db.add(result_obj)
        db.add(session)
        db.commit()
        logger.info(f"Session {interview_id} processing complete. Final score: {computed_score}")

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
