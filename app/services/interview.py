import os
import random
import json
from typing import Dict, Union, Optional, Any
from sqlmodel import Session, select
from ..models.db_models import Questions
from ..core.config import local_llm
from ..prompts.evaluation import evaluation_prompt
from ..prompts.code_evaluation import code_evaluation_prompt
from ..core.logger import get_logger
from huggingface_hub import InferenceClient
from groq import Groq

logger = get_logger(__name__)

# Modal integration flag (shared with audio.py)
USE_MODAL = os.getenv("USE_MODAL", "false").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq Client if key is available
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

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


def calculate_scaled_score(llm_score: Any, question_marks: float) -> float:
    """Scale a 0-10 LLM score to the question's marks with clamping and rounding."""
    try:
        llm_score = float(llm_score)
    except (ValueError, TypeError):
        llm_score = 0.0
    
    scaling_factor = float(question_marks) / 10.0
    final_score = llm_score * scaling_factor
    
    # Safeguards: Clamp to [0, marks] and round to 1 decimal place
    final_score_float = float(final_score)
    final_score_clamped = max(0.0, min(final_score_float, float(question_marks)))
    return round(final_score_clamped, 1)


def evaluate_answer_content(
    question: str,
    answer: str,
    response_type: str = "text",
    question_title: str = "",
    question_marks: float = 10.0,
) -> Dict[str, Union[str, float]]:
    """Evaluate interview answer using LLM with retry logic and scaling.
    
    Uses Modal if enabled, else falls back through Groq → HF → local Ollama.
    Retries up to 2 times on failure.
    """
    if response_type == "code":
        return evaluate_code_submission(
            problem_title=question_title or "Coding Problem",
            problem_statement=question,
            code=answer,
            question_marks=question_marks,
        )

    def _parse_llm_result(raw_content: str) -> Optional[dict]:
        """Try to parse JSON and normalize keys."""
        try:
            # Handle markdown code blocks if present
            clean_content = raw_content.strip()
            if clean_content.startswith("```"):
                lines = clean_content.split('\n')
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].strip() == "```": lines = lines[:-1]
                clean_content = "\n".join(lines).strip()
            
            data = json.loads(clean_content)
            # Normalize keys
            feedback = data.get("feedback") or data.get("reason") or ""
            score_raw = data.get("score_out_of_10")
            if score_raw is None:
                score_raw = data.get("score", 5.0)
            
            return {
                "feedback": feedback,
                "score": calculate_scaled_score(score_raw, question_marks)
            }
        except Exception:
            return None

    for attempt in range(2):
        logger.info(f"Evaluation attempt {attempt + 1}/2 for question: {question[:50]}...")
        
        # 1. Try Modal if enabled
        if USE_MODAL:
            evaluator_cls = get_modal_evaluator()
            if evaluator_cls:
                try:
                    result = evaluator_cls().evaluate.remote(question, answer)
                    parsed = _parse_llm_result(json.dumps(result))
                    if parsed: return parsed
                except Exception as e:
                    logger.warning(f"Modal attempt {attempt + 1} failed: {e}")

        # 2. Groq Fallback
        if groq_client:
            try:
                system_instruction = (
                    "You are an expert technical interviewer. Evaluate the candidate's answer. "
                    "Provide constructive feedback. Return a JSON object with "
                    "'feedback' (string) and 'score_out_of_10' (float 0-10)."
                )
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"Question: {question}\n\nYour Answer: {answer}"}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                parsed = _parse_llm_result(completion.choices[0].message.content)
                if parsed:
                    logger.info(f"✅ Groq evaluation successful on attempt {attempt + 1}")
                    return parsed
            except Exception as e:
                logger.warning(f"Groq attempt {attempt + 1} failed: {e}")

        # 3. HF / local fallback
        try:
            # Try HF if token exists
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                try:
                    client = InferenceClient(token=hf_token)
                    response = client.chat_completion(
                        model="Qwen/Qwen2.5-7B-Instruct",
                        messages=[
                            {"role": "system", "content": "Return JSON with 'feedback' and 'score_out_of_10' (0-10)."},
                            {"role": "user", "content": f"Q: {question}\nA: {answer}"}
                        ],
                        max_tokens=512,
                        temperature=0.1
                    )
                    parsed = _parse_llm_result(response.choices[0].message.content)
                    if parsed: return parsed
                except Exception as e:
                    logger.warning(f"HF attempt {attempt + 1} failed: {e}")

            # Local fallback (Ollama via LangChain)
            response = evaluation_chain.invoke({"question": question, "answer": answer})
            parsed = _parse_llm_result(response.content)
            if parsed: return parsed
            
        except Exception as e:
            logger.error(f"Fallback attempt {attempt + 1} failed: {e}")

    # If all attempts fail
    logger.error("All evaluation attempts failed. Using default 50% score.")
    return {
        "feedback": "Automated evaluation was unable to process your answer currently. A default score has been applied.",
        "score": calculate_scaled_score(5.0, question_marks),
        "error": True
    }


# ---------------------------------------------------------------------------
# Code Submission Evaluation
# ---------------------------------------------------------------------------

def evaluate_code_submission(
    problem_title: str,
    problem_statement: str,
    code: str,
    question_marks: float = 10.0,
) -> Dict[str, Union[str, float]]:
    """Evaluate a candidate's code submission for a coding problem.
    
    Returns a dict with: feedback, score, correctness, time_complexity,
    space_complexity, issues.
    """
    import json as _json

    def _scale_code_result(result_dict: dict) -> dict:
        """Helper to scale score and ensure all keys exist."""
        score_raw = result_dict.get("score", 0.0)
        # Assuming code LLM returns score out of 10 by default
        result_dict["score"] = calculate_scaled_score(score_raw, question_marks)
        result_dict.setdefault("correctness", "unknown")
        result_dict.setdefault("time_complexity", "unknown")
        result_dict.setdefault("space_complexity", "unknown")
        result_dict.setdefault("issues", [])
        return result_dict

    def _chain_invoke(chain, vars_: dict) -> dict:
        """Run chain and parse JSON response."""
        raw = chain.invoke(vars_).content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            raw = "\n".join(lines).strip()
        try:
            return _json.loads(raw)
        except _json.JSONDecodeError:
            return {
                "feedback": raw,
                "score": 0.0,
                "correctness": "unknown",
                "time_complexity": "unknown",
                "space_complexity": "unknown",
                "issues": [],
            }

    chain_vars = {
        "title": problem_title,
        "problem_statement": problem_statement,
        "code": code,
    }

    code_eval_chain = code_evaluation_prompt | local_llm

    # --- Groq Fallback (High Speed) ---
    if groq_client:
        try:
            logger.info("evaluate_code: Attempting Groq API...")
            system_instruction = (
                "You are an expert technical interviewer. Evaluate the candidate's code. "
                "Provide feedback on correctness, complexity, and issues. "
                "Return a JSON object with 'feedback' (string), 'score' (float 0-10), "
                "'correctness' (string), 'time_complexity' (string), "
                "'space_complexity' (string), and 'issues' (array of strings)."
            )
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Problem: {problem_title}\nStatement: {problem_statement}\nCode: {code}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            result = _json.loads(completion.choices[0].message.content)
            logger.info(f"evaluate_code: Groq API score={result.get('score')}")
            return _scale_code_result(result)
        except Exception as e:
            logger.warning(f"evaluate_code: Groq API failed: {e}")

    # --- Hugging Face Inference API ---
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            logger.info("evaluate_code: Attempting HF Inference API...")
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token)
            model_id = "Qwen/Qwen2.5-7B-Instruct"
            rendered = code_evaluation_prompt.format_messages(**chain_vars)
            role_map = {"system": "system", "human": "user", "ai": "assistant"}
            messages = [
                {"role": role_map.get(m.type if hasattr(m, "type") else "user", "user"), "content": m.content}
                for m in rendered
            ]
            response = client.chat_completion(
                model=model_id, messages=messages, max_tokens=1024, temperature=0.1
            )
            content = response.choices[0].message.content
            if content.startswith("```"):
                lines = content.split("\n")
                lines = [l for l in lines if not l.startswith("```")]
                content = "\n".join(lines).strip()
            result = _json.loads(content)
            logger.info(f"evaluate_code: HF API score={result.get('score')}")
            return _scale_code_result(result)
        except Exception as e:
            logger.warning(f"evaluate_code: HF API failed: {e}")

    # --- Local Ollama fallback ---
    try:
        logger.info("evaluate_code: Using local Ollama...")
        result = _chain_invoke(code_eval_chain, chain_vars)
        logger.info(f"evaluate_code: Ollama score={result.get('score')}")
        return _scale_code_result(result)
    except Exception as e:
        logger.error(f"evaluate_code: Ollama failed: {e}")
        return _scale_code_result({
            "feedback": "Code evaluation service temporarily unavailable.",
            "score": 0.0,
            "error": True,
        })


# ---------------------------------------------------------------------------
# Coding Question Generation
# ---------------------------------------------------------------------------

def generate_coding_questions_from_prompt(
    ai_prompt: str,
    difficulty_mix: str,
    num_questions: int,
) -> list[dict]:
    """Generate LeetCode-style coding problems using LLM.
    
    Returns a list of question dicts with keys:
    title, problem_statement, examples, constraints, starter_code,
    topic, difficulty, marks, response_type.

    Falls back through: Hugging Face Inference API → local Ollama.
    Raises ValueError if no questions can be generated.
    """
    import json as _json
    from ..prompts.coding_question_generation import coding_question_generation_prompt

    generation_chain = coding_question_generation_prompt | local_llm
    rendered_messages = coding_question_generation_prompt.format_messages(
        ai_prompt=ai_prompt,
        difficulty_mix=difficulty_mix,
        num_questions=num_questions,
    )

    def _parse_json(raw: str) -> list[dict]:
        content = raw.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            content = "\n".join(lines).strip()
        data = _json.loads(content)
        if not isinstance(data, list):
            raise ValueError("LLM did not return a JSON array")
        return data

    last_error = None

    # --- Groq API ---
    if groq_client:
        try:
            logger.info("generate_coding_questions: Attempting Groq API...")
            system_instruction = (
                "You are an expert technical interviewer. Generate LeetCode-style coding problems in JSON format. "
                "Return a JSON array of objects with: 'title', 'problem_statement', 'examples', 'constraints', "
                "'starter_code', 'topic', 'difficulty', 'marks', and 'response_type' (set to 'code')."
            )
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Topic/Prompt: {ai_prompt}\nDifficulty Mix: {difficulty_mix}\nNum: {num_questions}"}
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            result = _parse_json(content)
            if isinstance(result, dict) and "questions" in result:
                result = result["questions"]
            if isinstance(result, list):
                logger.info(f"generate_coding_questions: Groq API returned {len(result)} problems")
                return result
        except Exception as e:
            last_error = f"Groq API failed: {str(e)}"
            logger.warning(last_error)

    # --- Hugging Face Inference API ---
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        try:
            logger.info("generate_coding_questions: Attempting HF Inference API...")
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=hf_token)
            model_id = "Qwen/Qwen2.5-7B-Instruct"
            role_map = {"system": "system", "human": "user", "ai": "assistant"}
            messages = [
                {"role": role_map.get(m.type if hasattr(m, "type") else "user", "user"), "content": m.content}
                for m in rendered_messages
            ]
            response = client.chat_completion(
                model=model_id, messages=messages, max_tokens=4096, temperature=0.4
            )
            content = response.choices[0].message.content
            result = _parse_json(content)
            logger.info(f"generate_coding_questions: HF API returned {len(result)} problems")
            return result
        except Exception as e:
            last_error = f"HF API failed: {str(e)}"
            logger.warning(last_error)

    # --- Local Ollama ---
    try:
        logger.info("generate_coding_questions: Using local Ollama...")
        response = generation_chain.invoke({
            "ai_prompt": ai_prompt,
            "difficulty_mix": difficulty_mix,
            "num_questions": num_questions,
        })
        result = _parse_json(response.content)
        logger.info(f"generate_coding_questions: Ollama returned {len(result)} problems")
        return result
    except Exception as e:
        error_msg = f"Ollama failed: {str(e)}"
        if last_error:
            error_msg = f"{last_error} | {error_msg}"
        logger.error(error_msg)
        raise ValueError(f"Coding question generation failed: {error_msg}")


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

    def _parse_json(raw: str) -> Union[list, dict]:
        """Strip markdown fences and parse JSON."""
        content = raw.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].strip() == "```": lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}\nContent: {content}")
            raise ValueError(f"LLM returned invalid JSON: {str(e)}")

    last_error = None

    # --- Groq API ---
    if groq_client:
        try:
            logger.info("generate_questions: Attempting Groq API...")
            system_instruction = (
                "You are an expert technical interviewer. Generate interview questions in JSON format. "
                "Return a JSON array of objects where each object has: "
                "'question_text' (string), 'topic' (string), 'difficulty' (string: Easy/Medium/Hard), "
                "'marks' (int), and 'response_type' (string: text)."
            )
            
            # Using the same llama-3.3-70b-versatile for high quality
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Topic: {ai_prompt}\nYears of Experience: {years_of_experience}\nNumber of Questions: {num_questions}"}
                ],
                temperature=0.6, # Slightly higher temperature for variety in questions
                max_completion_tokens=4096, # 20 questions might need more tokens
                top_p=1,
                stream=False,
                response_format={"type": "json_object"} if num_questions > 1 else None, # JSON mode if possible
            )
            
            content = completion.choices[0].message.content
            # If JSON mode was used, it might be wrapped in an object depending on prompt
            # But the prompt asks for a JSON array. 
            # Note: Groq with response_format={"type": "json_object"} requires the word "json" in the prompt
            # and returns a JSON object, not a raw array.
            
            result = _parse_json(content)
            # If result is a dict, extract the questions list
            if isinstance(result, dict):
                if "questions" in result:
                    result = result["questions"]
                elif "data" in result: # and "data" ...
                    result = result["data"]
                else:
                    # If it's a dict but no obvious key, maybe it's just one question?
                    # Or check for any list value
                    for val in result.values():
                        if isinstance(val, list):
                            result = val
                            break
            
            if isinstance(result, list):
                logger.info(f"generate_questions: Groq API returned {len(result)} questions")
                return result
            else:
                logger.error(f"Groq returned non-list result: {result}")
                raise ValueError("AI service returned an unexpected response format.")
        except Exception as e:
            last_error = f"Groq API failed: {str(e)}"
            logger.warning(last_error)

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
