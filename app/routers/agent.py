"""
Agent Interview Router
======================
Prefix  : /api/agent
Tag     : Agent Interview

Endpoints
---------
POST  /start                       — Start a new AI-agent interview session
POST  /respond                     — Submit a candidate answer, get next question
POST  /finish/{session_id}         — Mark session complete
GET   /conversation/{session_id}   — Retrieve the full conversation transcript
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timezone

from ..core.database import get_db
from ..core.logger import get_logger
from ..models.db_models import AgentSession, AgentConversationTurn
from ..agents.interviewer_agent import (
    DEFAULT_QUESTIONS,
    get_next_question,
    is_interview_complete,
)
from ..schemas.api_response import ApiResponse

router = APIRouter(prefix="/agent", tags=["Agent Interview"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class StartAgentInterviewRequest(BaseModel):
    candidate_name: str
    job_role: Optional[str] = "General"


class RespondRequest(BaseModel):
    session_id: int
    answer: str


# ---------------------------------------------------------------------------
# Helper: convert DB turns into plain dicts for the agent logic
# ---------------------------------------------------------------------------

def _turns_to_dicts(turns: list) -> list:
    return [{"speaker": t.speaker, "message": t.message} for t in sorted(turns, key=lambda x: x.turn_index)]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/start",
    response_model=ApiResponse[dict],
    summary="Start a new AI-agent interview",
)
async def start_agent_interview(
    body: StartAgentInterviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates a new AgentSession and delivers the first question
    ("Tell me about yourself.") without any LLM call.
    """
    # Create session
    agent_session = AgentSession(
        candidate_name=body.candidate_name,
        job_role=body.job_role or "General",
        status="active",
    )
    db.add(agent_session)
    db.commit()
    db.refresh(agent_session)

    # First question — always verbatim, no LLM needed
    first_question = DEFAULT_QUESTIONS[0]
    turn = AgentConversationTurn(
        session_id=agent_session.id,
        turn_index=0,
        speaker="agent",
        message=first_question,
    )
    db.add(turn)
    db.commit()

    logger.info(f"Agent session {agent_session.id} started for '{body.candidate_name}'")

    return ApiResponse(
        status_code=200,
        message="Agent interview started successfully",
        data={
            "session_id": agent_session.id,
            "candidate_name": agent_session.candidate_name,
            "job_role": agent_session.job_role,
            "question": first_question,
            "question_number": 1,
            "total_questions": len(DEFAULT_QUESTIONS),
            "is_finished": False,
        },
    )


@router.post(
    "/respond",
    response_model=ApiResponse[dict],
    summary="Submit a candidate answer and receive the next question",
)
async def respond_to_agent(
    body: RespondRequest,
    db: Session = Depends(get_db),
):
    """
    Saves the candidate's answer as a conversation turn, then uses the agent
    to generate and return the next question. Returns `is_finished: true`
    when all questions have been asked.
    """
    # Fetch session
    agent_session = db.get(AgentSession, body.session_id)
    if not agent_session:
        raise HTTPException(status_code=404, detail="Agent session not found")
    if agent_session.status == "completed":
        raise HTTPException(status_code=400, detail="This interview session has already been completed")

    # Load existing turns
    existing_turns = db.exec(
        select(AgentConversationTurn)
        .where(AgentConversationTurn.session_id == body.session_id)
        .order_by(AgentConversationTurn.turn_index)
    ).all()

    # Save candidate answer
    next_index = len(existing_turns)
    candidate_turn = AgentConversationTurn(
        session_id=body.session_id,
        turn_index=next_index,
        speaker="candidate",
        message=body.answer.strip(),
    )
    db.add(candidate_turn)
    db.commit()

    # Build history for agent logic (including the just-saved answer)
    all_turns = list(existing_turns) + [candidate_turn]
    history = _turns_to_dicts(all_turns)

    # Check if interview is done
    if is_interview_complete(history):
        return ApiResponse(
            status_code=200,
            message="All questions answered. Call /finish to complete the interview.",
            data={
                "session_id": body.session_id,
                "question": None,
                "is_finished": True,
                "question_number": len(DEFAULT_QUESTIONS),
                "total_questions": len(DEFAULT_QUESTIONS),
            },
        )

    # Generate next question via agent
    next_q = get_next_question(history)
    if next_q is None:
        return ApiResponse(
            status_code=200,
            message="All questions answered. Call /finish to complete the interview.",
            data={
                "session_id": body.session_id,
                "question": None,
                "is_finished": True,
                "question_number": len(DEFAULT_QUESTIONS),
                "total_questions": len(DEFAULT_QUESTIONS),
            },
        )

    # Save agent's next question turn
    agent_turn = AgentConversationTurn(
        session_id=body.session_id,
        turn_index=next_index + 1,
        speaker="agent",
        message=next_q,
    )
    db.add(agent_turn)
    db.commit()

    # Count how many agent turns so far (= which question number we're on)
    agent_turn_count = sum(1 for t in all_turns if t.speaker == "agent") + 1

    logger.info(f"Agent session {body.session_id}: question {agent_turn_count}/{len(DEFAULT_QUESTIONS)}")

    return ApiResponse(
        status_code=200,
        message="Answer saved. Next question ready.",
        data={
            "session_id": body.session_id,
            "question": next_q,
            "is_finished": False,
            "question_number": agent_turn_count,
            "total_questions": len(DEFAULT_QUESTIONS),
        },
    )


@router.post(
    "/finish/{session_id}",
    response_model=ApiResponse[dict],
    summary="Finish and save the agent interview",
)
async def finish_agent_interview(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    Marks the session as completed and records the finish timestamp.
    After this, the conversation is frozen and available for human review.
    """
    agent_session = db.get(AgentSession, session_id)
    if not agent_session:
        raise HTTPException(status_code=404, detail="Agent session not found")
    if agent_session.status == "completed":
        return ApiResponse(
            status_code=200,
            message="Session was already completed",
            data={"session_id": session_id, "status": "completed"},
        )

    agent_session.status = "completed"
    agent_session.finished_at = datetime.now(timezone.utc)
    db.add(agent_session)
    db.commit()

    # Count total turns for summary
    turns = db.exec(
        select(AgentConversationTurn).where(AgentConversationTurn.session_id == session_id)
    ).all()

    logger.info(f"Agent session {session_id} completed. Total turns: {len(turns)}")

    return ApiResponse(
        status_code=200,
        message="Interview completed successfully. Transcript saved for review.",
        data={
            "session_id": session_id,
            "status": "completed",
            "total_turns": len(turns),
            "candidate_name": agent_session.candidate_name,
            "job_role": agent_session.job_role,
            "started_at": agent_session.started_at.isoformat(),
            "finished_at": agent_session.finished_at.isoformat(),
        },
    )


@router.get(
    "/conversation/{session_id}",
    response_model=ApiResponse[dict],
    summary="Get the full conversation transcript for human review",
)
async def get_conversation(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns the complete Q&A transcript in chronological order.
    Intended for admins / human evaluators to read and assess the candidate.
    """
    agent_session = db.get(AgentSession, session_id)
    if not agent_session:
        raise HTTPException(status_code=404, detail="Agent session not found")

    turns = db.exec(
        select(AgentConversationTurn)
        .where(AgentConversationTurn.session_id == session_id)
        .order_by(AgentConversationTurn.turn_index)
    ).all()

    transcript = [
        {
            "turn": t.turn_index,
            "speaker": t.speaker,
            "message": t.message,
            "timestamp": t.timestamp.isoformat(),
        }
        for t in turns
    ]

    return ApiResponse(
        status_code=200,
        message="Conversation transcript retrieved",
        data={
            "session_id": session_id,
            "candidate_name": agent_session.candidate_name,
            "job_role": agent_session.job_role,
            "status": agent_session.status,
            "started_at": agent_session.started_at.isoformat(),
            "finished_at": agent_session.finished_at.isoformat() if agent_session.finished_at else None,
            "total_turns": len(transcript),
            "transcript": transcript,
        },
    )
