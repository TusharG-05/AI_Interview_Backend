"""
InterviewerAgent: drives the AI-agent interview conversation.

Logic:
  1. Holds a hardcoded question pool.
  2. On each turn, it checks how many questions have been asked.
  3. Uses the LLM to ask the next question naturally (with brief ack of previous answer).
  4. When all questions are exhausted, signals the interview is finished.
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default question pool (first question is always the opener)
# ---------------------------------------------------------------------------
DEFAULT_QUESTIONS: List[str] = [
    "Tell me about yourself.",
    "What are your biggest strengths and weaknesses?",
    "Describe a challenging project you worked on and how you overcame the difficulties.",
    "Where do you see yourself in 5 years?",
]


def _build_history_text(turns: list) -> str:
    """Convert a list of turn dicts {speaker, message} into a readable transcript."""
    if not turns:
        return "(No conversation yet)"
    lines = []
    for t in turns:
        label = "Interviewer" if t["speaker"] == "agent" else "Candidate"
        lines.append(f"{label}: {t['message']}")
    return "\n".join(lines)


def get_next_question(
    turns: list,
    question_pool: List[str] = DEFAULT_QUESTIONS,
) -> Optional[str]:
    """
    Determine and return the next question string, or None if all done.

    `turns` is a list of dicts with keys: {speaker: str, message: str}
    """
    # Count how many questions the agent has already asked
    agent_turns = [t for t in turns if t["speaker"] == "agent"]
    asked_count = len(agent_turns)

    if asked_count >= len(question_pool):
        # All questions have been asked
        return None

    raw_question = question_pool[asked_count]

    # For the very first question, return verbatim (no prior context to acknowledge)
    if asked_count == 0:
        return raw_question

    # For subsequent questions, ask the LLM to phrase it naturally
    try:
        from ..core.config import local_llm
        from ..prompts.agent import agent_question_prompt

        history_text = _build_history_text(turns)
        chain = agent_question_prompt | local_llm
        response = chain.invoke({
            "history": history_text,
            "next_question": raw_question,
        })
        phrased = response.content.strip()
        if phrased:
            return phrased
        return raw_question  # Fallback if LLM returns empty
    except Exception as e:
        logger.warning(f"InterviewerAgent LLM call failed, using raw question. Error: {e}")
        return raw_question  # Graceful degradation: use verbatim question


def is_interview_complete(turns: list, question_pool: List[str] = DEFAULT_QUESTIONS) -> bool:
    """Returns True if all questions have been asked."""
    agent_turns = [t for t in turns if t["speaker"] == "agent"]
    return len(agent_turns) >= len(question_pool)
