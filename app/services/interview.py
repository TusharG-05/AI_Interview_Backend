import os
import random
import json
import re
from typing import Dict, Union, Optional, Any
from sqlmodel import Session, select
from ..models.db_models import Questions
from ..core.config import local_llm, IS_ORCHESTRATOR, USE_MODAL
from ..prompts.evaluation import evaluation_prompt
from ..prompts.code_evaluation import code_evaluation_prompt
from ..core.logger import get_logger
from ..core.ai_clients import get_groq_client, call_llm, GROQ_MODEL
from huggingface_hub import InferenceClient

logger = get_logger(__name__)

# Single source of truth for the evaluation system prompt used across all LLM backends.
STRICT_EVAL_SYSTEM_PROMPT = (
    "You are a strict but fair technical interviewer evaluating a candidate's answer. "
    "SCORING RULES: "
    "(1) Score range: 0.0 to 10.0 ONLY — never go above 10.0. "
    "(2) COMPLETELY WRONG answer → 0.0. Factually incorrect, irrelevant, or off-topic answers get 0. "
    "(3) PARTIALLY CORRECT → proportional score. If the candidate covers half the key points correctly, give ~5/10. "
    "(4) FULLY CORRECT → 10.0. A concise, accurate answer is a perfect answer. Do NOT penalize for brevity. "
    "(5) NON-ANSWERS → 0.0. 'I don't know', off-topic, or asking a question back = 0. "
    "(6) STRICTLY match score to quality — do NOT give charity marks for vague or wrong guesses. "
    "FEEDBACK RULES: Address the user as 'You'/'Your'. Never say 'the candidate'. "
    "NEVER reveal the correct answer or model answer. You may point out where the mistake is, but you MUST NOT tell them what the correct answer should be or how to correct it. "
    "Give concise coaching feedback focused only on what they got wrong or what was missing, without providing the actual solution. "
    "Return a valid JSON object with exactly two keys: 'feedback' (string) and 'score_out_of_10' (float 0-10). "
    "Respond ONLY with a valid JSON object. Do not include any text or explanations outside the JSON object."
)

# Initialize Groq Client lazily via centralized ai_clients
def get_interview_groq():
    return get_groq_client()

# Chain initialization (moved inside functions for lazy loading)



# Lazy load Modal LLM
_modal_evaluator = None
_modal_lookup_error = None

def get_modal_evaluator():
    """Lazy load Modal LLM evaluator via remote reference."""
    global _modal_evaluator, _modal_lookup_error
    if _modal_evaluator is None:
        try:
            # pyrefly: ignore [missing-import]
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


# Marks assigned per difficulty level for AI-generated questions
THEORY_MARKS_BY_DIFFICULTY: dict[str, int] = {"Easy": 1, "Medium": 3, "Hard": 5}
CODING_MARKS_BY_DIFFICULTY: dict[str, int] = {"Easy": 10, "Medium": 15, "Hard": 20}



def calculate_scaled_score(llm_score: Any, question_marks: float) -> int:
    """Scale a 0-10 LLM score to the question's marks, clamped and returned as int.
    
    The rounding happens BEFORE the final clamp to prevent any rounding artifact
    from pushing the score above the question's maximum marks.
    """
    if isinstance(llm_score, str):
        import re
        match = re.search(r"(\d+(?:\.\d+)?)", llm_score)
        if match:
            llm_score = match.group(1)
            
    try:
        llm_score = float(llm_score)
    except (ValueError, TypeError):
        llm_score = 0.0
    
    # Clamp LLM score to [0, 10] first (guards against hallucinated scores like 13/10)
    llm_score = max(0.0, min(llm_score, 10.0))
    
    scaling_factor = float(question_marks) / 10.0
    final_score = llm_score * scaling_factor
    
    # Round first, then clamp — this prevents int(round()) from ever exceeding question_marks
    rounded = int(round(final_score))
    logger.info(f"rounded score is: {rounded}")
    logger.info(f"FINAL SCORE IS : {final_score}")
    logger.info(f"final answer: {max(0, min(rounded, int(question_marks)))}")
    print(f"--- DEBUG --- rounded: {rounded}, final_score: {final_score}, ans: {question_marks}")
    return max(0, min(rounded, int(question_marks)))


def _safe_feedback_from_score(score_out_of_10: Any) -> str:
    """Fallback coaching feedback when model feedback is empty or fully unsafe."""
    try:
        s = float(score_out_of_10)
    except (TypeError, ValueError):
        s = 5.0

    if s >= 8.0:
        return (
            "Your answer is strong overall. Keep your explanation structured and verify key details before submitting."
        )
    if s >= 6.0:
        return (
            "Your answer is partially correct. Improve precision and explain your reasoning more clearly."
        )
    if s >= 4.0:
        return (
            "Your answer needs improvement. Focus on the core concept and organize your response step-by-step."
        )
    return (
        "Your answer is currently incorrect or incomplete. Revisit the fundamentals and answer with clearer reasoning."
    )


def _extract_target_term(question: str) -> str:
    """Extract the main concept from definition-style questions."""
    q = re.sub(r"\s+", " ", (question or "").strip().lower())
    patterns = [
        r"^what\s+is\s+an?\s+(.+?)\??$",
        r"^what\s+are\s+(.+?)\??$",
        r"^define\s+(.+?)\??$",
        r"^explain\s+(.+?)\??$",
    ]
    for pattern in patterns:
        m = re.match(pattern, q)
        if m:
            term = m.group(1).strip(" .?")
            # Remove trailing context words that are usually not part of the term.
            term = re.sub(r"\s+in\s+python$", "", term).strip()
            term = re.sub(r"^(a|an|the)\s+", "", term).strip()
            return term
    return ""


def _contains_target_keyword(sentence_lower: str, target_term: str) -> bool:
    """Check if sentence mentions target concept keywords with simple singular/plural matching."""
    if not target_term:
        return False

    stop_words = {"a", "an", "the", "of", "in", "on", "for", "to", "and", "or"}
    keywords = [w for w in re.findall(r"[a-zA-Z]+", target_term.lower()) if w not in stop_words and len(w) >= 4]
    for kw in keywords:
        # Match both singular/plural forms for common cases (decorator/decorators).
        if re.search(rf"\b{re.escape(kw)}s?\b", sentence_lower):
            return True
    return False


def _is_pronoun_definition(sentence_lower: str) -> bool:
    """Check if sentence looks like a definition starting with pronoun/article (it/they/this/that are/is...)."""
    # Pattern: (pronoun/article) + (definition verb) = likely defining something mentioned before
    pattern = r"^(it|they|this|that|these|those|such|one)\s+(are|is|can be|refers to|means|defines)"
    return bool(re.match(pattern, sentence_lower.strip()))


def _sanitize_feedback_no_answer_leak(feedback: str, score_out_of_10: Any, question: str) -> str:
    """Keep dynamic feedback but remove answer-revealing statements.

    Additionally, ensure the feedback addresses the user directly by replacing any
    occurrence of "The Candidate response" (case‑insensitive) with "Your response".
    We also replace generic "the candidate" mentions with "you" where appropriate.
    """
    if not feedback or not str(feedback).strip():
        return _safe_feedback_from_score(score_out_of_10)

    clean = re.sub(r"\s+", " ", str(feedback)).strip()

    # If model emitted code blocks/solutions, do not return them.
    if "```" in clean:
        return _safe_feedback_from_score(score_out_of_10)

    leak_patterns = [
        r"\b(correct|ideal|expected|model|sample)\s+answer\b",
        r"\bthe\s+answer\s+is\b",
        r"\b(correct\s+response|best\s+answer|correct\s+result)\b",
        r"\byou\s+should\s+(have\s+)?answered\b",
        r"\bhere('?s|\s+is)\s+the\s+answer\b",
    ]
    definition_verbs = [
        " is ", " are ", " means ", " refers to ", " can be defined as ", " is defined as ", " used to "
    ]
    target_term = _extract_target_term(question)
    is_definition_question = bool(target_term)  # If we extracted a term, it's a definition question

    sentences = re.split(r"(?<=[.!?])\s+", clean)
    safe_sentences = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        lowered = s.lower()
        if any(re.search(pattern, lowered) for pattern in leak_patterns):
            continue

        # Semantic leak guard: for definition-style questions, drop sentences that define or describe the target term.
        if target_term and _contains_target_keyword(lowered, target_term) and any(v in lowered for v in definition_verbs):
            continue
        
        # Pronoun-based definition guard: for definition questions, drop sentences like "They are..." or "It is..."
        # that follow directly after mentioning the concept (these are typically answer-defining sentences)
        if is_definition_question and _is_pronoun_definition(lowered) and any(v in lowered for v in definition_verbs):
            continue

        safe_sentences.append(s)

    if not safe_sentences:
        return _safe_feedback_from_score(score_out_of_10)

    sanitized = " ".join(safe_sentences).strip()
    # Replace third‑person candidate phrasing with second‑person wording
    sanitized = re.sub(r"(?i)\bthe candidate response\b", "Your response", sanitized)
    sanitized = re.sub(r"(?i)\bthe candidate\b", "you", sanitized)
    if len(sanitized) > 500:
        sanitized = sanitized[:500].rsplit(" ", 1)[0].rstrip(".,;: ") + "."
    return sanitized


def _augment_feedback(parsed: dict, answer: str, question: str) -> dict:
    """Append a gentle hint about missing key concepts without revealing solution.

    The hint is added only when the extracted target term from the question is
    not present in the user's answer (checked via `_contains_target_keyword`).
    This keeps feedback constructive while avoiding direct answer leakage.
    """
    if not parsed:
        return parsed
    feedback = parsed.get("feedback", "")
    target_term = _extract_target_term(question)
    if target_term and not _contains_target_keyword(answer.lower(), target_term):
        hint = f" You missed mentioning the key concept '{target_term}'."
        if hint.strip() not in feedback:
            feedback = feedback.rstrip('.') + '.' + hint
        parsed["feedback"] = feedback
    return parsed


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
            feedback_raw = str(data.get("feedback") or data.get("reason") or "").strip()
            
            # Clean up hallucinated prefixes/suffixes
            feedback_raw = re.sub(r"^feedback:\s*", "", feedback_raw, flags=re.IGNORECASE)
            feedback_raw = re.sub(r"\s*score_out_of_10:\s*\d+(\.\d+)?\s*$", "", feedback_raw, flags=re.IGNORECASE)
            score_raw = data.get("score_out_of_10")
            if score_raw is None:
                score_raw = data.get("score", 5.0)

            safe_feedback = _sanitize_feedback_no_answer_leak(feedback_raw, score_raw, question)
            if feedback_raw and safe_feedback != str(feedback_raw).strip():
                logger.info("Evaluation feedback sanitized to prevent answer leakage.")
            
            return {
                "feedback": safe_feedback,
                "score": calculate_scaled_score(score_raw, question_marks),
                "score_out_of_10": float(score_raw)
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    import time
    for attempt in range(2):
        if attempt > 0:
            sleep_time = 2 ** attempt
            logger.info(f"Retrying evaluation in {sleep_time} seconds (attempt {attempt + 1}/2)...")
            time.sleep(sleep_time)
            
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
        groq_client = get_interview_groq()
        if groq_client:
            try:
                completion = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": STRICT_EVAL_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Question: {question}\n\nCandidate's Answer: {answer}"}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                parsed = _parse_llm_result(completion.choices[0].message.content)
                if parsed:
                    parsed = _augment_feedback(parsed, answer, question)
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
                            {"role": "system", "content": STRICT_EVAL_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Question: {question}\n\nCandidate's Answer: {answer}"}
                        ],
                        max_tokens=512,
                        temperature=0.1
                    )
                    parsed = _parse_llm_result(response.choices[0].message.content)
                    if parsed:
                        parsed = _augment_feedback(parsed, answer, question)
                        return parsed
                except Exception as e:
                    logger.warning(f"HF attempt {attempt + 1} failed: {e}")

            # Local fallback (Ollama via LangChain) - Skip in Orchestrator mode to avoid timeout
            if not IS_ORCHESTRATOR:
                evaluation_chain = evaluation_prompt | local_llm
                response = evaluation_chain.invoke({"question": question, "answer": answer})
                parsed = _parse_llm_result(response.content)
                if parsed:
                    # Add hint about missing key concept if applicable
                    parsed = _augment_feedback(parsed, answer, question)
                    return parsed
            else:
                logger.warning("Orchestrator mode: Skipping local LLM fallback.")

            
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


def _chain_invoke_code(chain, vars_: dict) -> dict:
    """Run a LangChain chain and parse JSON response for code evaluation."""
    import json as _json
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
        """Scale score and ensure all keys exist."""
        score_raw = result_dict.get("score")
        if score_raw is None:
            score_raw = result_dict.get("score_out_of_10", 0.0)
        result_dict["score"] = calculate_scaled_score(score_raw, question_marks)
        result_dict["score_out_of_10"] = float(score_raw)
        result_dict.setdefault("correctness", "unknown")
        result_dict.setdefault("time_complexity", "unknown")
        result_dict.setdefault("space_complexity", "unknown")
        result_dict.setdefault("issues", [])
        return result_dict

    def _augment_code_feedback(parsed: dict, submitted_code: str) -> dict:
        """Append hints about missing semicolons/line-endings to LLM feedback.

        Uses a simple heuristic: statement-like lines in C/Java/JS-style
        languages that don't end with ';' are flagged as potentially missing
        a terminating semicolon.
        """
        if not parsed:
            return parsed
        feedback = parsed.get("feedback", "")
        missing_semicolons = []
        for i, ln in enumerate(submitted_code.splitlines(), start=1):
            stripped = ln.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("#"):
                continue
            if ("(" in stripped or "=" in stripped) and not stripped.endswith(";"):
                missing_semicolons.append(i)
        if missing_semicolons:
            hint = (
                f" It looks like line(s) {', '.join(map(str, missing_semicolons))}"
                " may be missing a terminating semicolon."
            )
            if hint.strip() not in feedback:
                feedback = feedback.rstrip(".") + "." + hint
            parsed["feedback"] = feedback
        return parsed


    chain_vars = {
        "title": problem_title,
        "problem_statement": problem_statement,
        "code": code,
    }

    code_eval_chain = code_evaluation_prompt | local_llm

    # --- Groq Fallback (High Speed) ---
    groq_client = get_interview_groq()
    if groq_client:
        try:
            logger.info("evaluate_code: Attempting Groq API...")
            system_instruction = (
                "You are an expert technical interviewer. Evaluate the code submission. "
                "Address the user directly as 'You' and 'Your' in your feedback (e.g., 'Your code is...'). "
                "Provide constructive feedback. Return a JSON object with 'feedback' (string), "
                "'score' (float 0-10), 'correctness' (string), 'time_complexity' (string), "
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
    if not IS_ORCHESTRATOR:
        try:
            logger.info("evaluate_code: Using local Ollama...")
            result = _chain_invoke_code(code_eval_chain, chain_vars)
            logger.info(f"evaluate_code: Ollama score={result.get('score')}")
            return _scale_code_result(result)
        except Exception as e:
            logger.error(f"evaluate_code: Ollama failed: {e}")
            return _scale_code_result({
                "feedback": "Code evaluation service temporarily unavailable.",
                "score": 0.0,
                "error": True,
            })
    else:
        logger.warning("Orchestrator mode: Skipping local code evaluation.")
        return _scale_code_result({
            "feedback": "Code evaluation unavailable (Orchestrator Mode).",
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
    groq_client = get_interview_groq()

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
    if not IS_ORCHESTRATOR:
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
    else:
        logger.warning("Orchestrator mode: Skipping local coding question generation.")
        raise ValueError(f"Coding question generation failed: {last_error or 'Remote services unavailable and local fallback disabled in Orchestrator Mode'}")



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

    # Initialize Groq client
    groq_client = get_groq_client()

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
                "If the user provides multiple-choice options (A, B, C, D), you MUST preserve them verbatim inside the 'question_text'. DO NOT strip them out. "
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
    if not IS_ORCHESTRATOR:
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
    else:
        logger.warning("Orchestrator mode: Skipping local question generation.")
        raise ValueError(f"Question generation failed: {last_error or 'Remote services unavailable and local fallback disabled in Orchestrator Mode'}")

