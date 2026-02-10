import os
import random
import json
from typing import Dict, Union, Optional
from sqlmodel import Session, select
from ..models.db_models import Questions
from ..core.config import local_llm
from ..prompts.evaluation import evaluation_prompt
from ..core.logger import get_logger

logger = get_logger(__name__)

# Modal integration flag (shared with audio.py)
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"

evaluation_chain = evaluation_prompt | local_llm

# Lazy load Modal LLM
_modal_evaluator = None

def get_modal_evaluator():
    """Lazy load Modal LLM evaluator to avoid import errors when Modal not installed."""
    global _modal_evaluator
    if _modal_evaluator is None:
        try:
            from ..modal_llm import LLMEvaluator
            _modal_evaluator = LLMEvaluator()
            logger.info("Modal LLM evaluator loaded successfully")
        except ImportError as e:
            logger.warning(f"Modal LLM not available: {e}")
            return None
    return _modal_evaluator


def evaluate_answer_content(question: str, answer: str) -> Dict[str, Union[str, float]]:
    """Evaluate interview answer using LLM. Uses Modal if enabled, else local Ollama."""
    
    # Try Modal if enabled
    if USE_MODAL:
        evaluator = get_modal_evaluator()
        if evaluator:
            try:
                logger.info("Using Modal LLM for evaluation")
                result = evaluator.evaluate.remote(question, answer)
                logger.info(f"Modal evaluation complete. Score: {result.get('score', 'N/A')}")
                return result
            except Exception as e:
                logger.warning(f"Modal LLM failed, falling back to local: {e}")
    
    # Local Ollama fallback
    try:
        response = evaluation_chain.invoke({
            "question": question,
            "answer": answer
        })
        
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        logger.debug(f"LLM Evaluation Raw Response: '{response.content}'")
        
        try:
            result = json.loads(content)
            if "feedback" not in result:
                 result["feedback"] = str(content)
            if "score" not in result:
                 result["score"] = 0.5
            return result
        except json.JSONDecodeError:
            return {
                "feedback": response.content,
                "score": 0.5
            }
    except Exception as e:
        logger.error(f"LLM Service failure: {e}")
        return {
            "feedback": "Evaluation service currently unavailable. Please check later.",
            "score": 0.0,
            "error": True
        }


def get_or_create_question(session: Session, content: str, topic: str = "General", difficulty: str = "Unknown") -> Questions:
    """Finds a question by content or creates a new one."""
    stmt = select(Questions).where(Questions.content == content)
    question = session.exec(stmt).first()
    
    if not question:
        question = Questions(content=content, topic=topic, difficulty=difficulty)
        session.add(question)
        session.flush() # Get ID but don't commit yet
        session.refresh(question)
        
    return question

def get_custom_response(prompt: str) -> str:
    response = local_llm.invoke(prompt)
    return response.content
