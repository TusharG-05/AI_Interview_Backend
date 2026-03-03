import os
import random
import json
from typing import Dict, Union, Optional
from sqlmodel import Session, select
from ..models.db_models import Questions
from ..core.config import local_llm
from ..prompts.evaluation import evaluation_prompt
from ..core.logger import get_logger
from huggingface_hub import InferenceClient

logger = get_logger(__name__)

# Modal integration flag (shared with audio.py)
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"

evaluation_chain = evaluation_prompt | local_llm

# Lazy load Modal LLM
_modal_evaluator = None
_modal_lookup_error = None

def get_modal_evaluator():
    """Lazy load Modal LLM evaluator via remote reference."""
    global _modal_evaluator, _modal_lookup_error
    if _modal_evaluator is None:
        try:
            import modal
            # Check for tokens to provide better error messages
            if not os.getenv("MODAL_TOKEN_ID") or not os.getenv("MODAL_TOKEN_SECRET"):
                _modal_lookup_error = "MISSING_TOKENS: MODAL_TOKEN_ID or MODAL_TOKEN_SECRET not set in Environment/Secrets"
                logger.warning(_modal_lookup_error)
                return None

            # Use from_name for lazy reference to deployed class
            # Note: Deployment name is 'interview-llm-eval', Class name is 'LLMEvaluator'
            _modal_evaluator = modal.Cls.from_name("interview-llm-eval", "LLMEvaluator")
            logger.info("Modal LLM evaluator reference obtained via from_name")
            _modal_lookup_error = None
        except ImportError:
            _modal_lookup_error = "IMPORT_ERROR: 'modal' package not found"
            logger.warning(_modal_lookup_error)
            return None
        except Exception as e:
            _modal_lookup_error = f"LOOKUP_ERROR: {str(e)}"
            logger.warning(f"Modal LLM lookup failed: {e}")
            return None
    return _modal_evaluator


def evaluate_answer_content(question: str, answer: str) -> Dict[str, Union[str, float]]:
    """Evaluate interview answer using LLM. Uses Modal if enabled, else local Ollama."""
    
    last_error = None

    # Try Modal if enabled
    if USE_MODAL:
        evaluator_cls = get_modal_evaluator()
        if evaluator_cls:
            try:
                logger.info("Using Modal LLM for evaluation")
                # Instantiate the class before calling remote method
                result = evaluator_cls().evaluate.remote(question, answer)
                logger.info(f"Modal evaluation complete. Score: {result.get('score', 'N/A')}")
                return result
            except Exception as e:
                last_error = f"Modal LLM Execution failed: {str(e)}"
                logger.warning(last_error)
        else:
            # Direct access since we are in the same module
            last_error = f"Modal setup failed: {_modal_lookup_error or 'Unknown error'}"
            logger.warning(last_error)
    
    # Hugging Face Inference API Fallback
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            logger.info("Attempting Hugging Face Inference API fallback...")
            client = InferenceClient(token=hf_token)
            
            # Using Qwen 2.5 7B Instruct (same as Modal) for consistency
            model_id = "Qwen/Qwen2.5-7B-Instruct" 
            
            # Simple fallback prompt to avoid LangChain dependency issues
            system_instruction = (
                "You are an expert technical interviewer. Evaluate the candidate's answer. "
                "Return a JSON object with 'feedback' (string) and 'score' (float 0-10)."
            )
            
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Question: {question}\n\nCandidate's Answer: {answer}"}
            ]
            
            response = client.chat_completion(
                model=model_id, 
                messages=messages, 
                max_tokens=512,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Clean markdown if present
            if content.startswith("```"):
                lines = content.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            
            try:
                result = json.loads(content)
                if "feedback" not in result:
                    result["feedback"] = content
                if "score" not in result:
                    result["score"] = 5.0
                logger.info("✅ HF Inference API fallback successful")
                return result
            except json.JSONDecodeError:
                logger.warning("HF API returned non-JSON")
                return {
                    "feedback": content,
                    "score": 5.0
                }
                
        except Exception as e:
            fallback_error = f"HF Inference API failed: {str(e)}"
            logger.error(fallback_error)
            if last_error:
                last_error += f" | {fallback_error}"
            else:
                last_error = fallback_error

    
    # Local Ollama fallback
    try:
        if not USE_MODAL:
            logger.info("Using local Ollama for evaluation")

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
        error_msg = f"LLM Service failure: {str(e)}"
        if last_error:
            error_msg = f"{last_error} | Fallback failed: {str(e)}"
            
        logger.error(error_msg)
        return {
            "feedback": "Evaluation service currently unavailable. Please check later.",
            "score": 0.0,
            "error": True,
            "details": error_msg if USE_MODAL else "Local Ollama unreachable"
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


def generate_questions_from_prompt(
    ai_prompt: str,
    years_of_experience: int,
    num_questions: int,
) -> list[dict]:
    """
    Use the LLM to generate interview questions based on a topic/description.
    Returns a list of question dicts with keys:
    question_text, topic, difficulty, marks, response_type.

    Falls back through: Hugging Face Inference API → local Ollama.
    Raises ValueError if the LLM response cannot be parsed.
    """
    from ..prompts.question_generation import question_generation_prompt

    generation_chain = question_generation_prompt | local_llm

    # Build the rendered prompt string to use for the HF fallback
    rendered_messages = question_generation_prompt.format_messages(
        ai_prompt=ai_prompt,
        years_of_experience=years_of_experience,
        num_questions=num_questions,
    )

    def _parse_json(raw: str) -> list[dict]:
        """Strip markdown fences and parse JSON array."""
        content = raw.strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            content = "\n".join(lines).strip()
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("LLM did not return a JSON array")
        return data

    last_error = None

    # --- Hugging Face Inference API ---
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            logger.info("generate_questions: Attempting HF Inference API...")
            client = InferenceClient(token=hf_token)
            model_id = "Qwen/Qwen2.5-7B-Instruct"
            messages = [
                {"role": msg.type if hasattr(msg, "type") else "user", "content": msg.content}
                for msg in rendered_messages
            ]
            # Normalise role names for OpenAI-style API
            role_map = {"system": "system", "human": "user", "ai": "assistant"}
            messages = [
                {"role": role_map.get(m["role"], "user"), "content": m["content"]}
                for m in messages
            ]
            response = client.chat_completion(
                model=model_id,
                messages=messages,
                max_tokens=2048,
                temperature=0.4,
            )
            content = response.choices[0].message.content
            result = _parse_json(content)
            logger.info(f"generate_questions: HF API returned {len(result)} questions")
            return result
        except Exception as e:
            last_error = f"HF API failed: {str(e)}"
            logger.warning(last_error)

    # --- Local Ollama ---
    try:
        logger.info("generate_questions: Using local Ollama...")
        response = generation_chain.invoke({
            "ai_prompt": ai_prompt,
            "years_of_experience": years_of_experience,
            "num_questions": num_questions,
        })
        result = _parse_json(response.content)
        logger.info(f"generate_questions: Ollama returned {len(result)} questions")
        return result
    except Exception as e:
        error_msg = f"Ollama failed: {str(e)}"
        if last_error:
            error_msg = f"{last_error} | {error_msg}"
        logger.error(error_msg)
        raise ValueError(f"Question generation failed: {error_msg}")
