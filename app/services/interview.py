import random
import json
from typing import Dict, Union, Optional
from sqlmodel import Session, select
from ..models.db_models import Questions
from ..core.config import local_llm
from ..prompts.evaluation import evaluation_prompt

evaluation_chain = evaluation_prompt | local_llm

def evaluate_answer_content(question: str, answer: str) -> Dict[str, Union[str, float]]:
    try:
        response = evaluation_chain.invoke({
            "question": question,
            "answer": answer
        })
        
        content = response.content.strip()
        if content.startswith("```"):
            # Strip markdown markers if present
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        print(f"DEBUG: LLM Evaluation Raw Response: '{response.content}'")
        print(f"DEBUG: Cleaned Content for JSON: '{content}'")
        
        try:
            # Attempt to parse JSON from the cleaned content
            result = json.loads(content)
            # Ensure keys exist
            if "feedback" not in result:
                 result["feedback"] = str(content)
            if "score" not in result:
                 result["score"] = 0.5 # Default middle score if missing
                 
            print(f"DEBUG: Parsed Score: {result['score']}")
            return result
        except json.JSONDecodeError:
            print("DEBUG: JSON parsing failed, returning fallback result.")
            # Fallback if LLM fails to return valid JSON
            return {
                "feedback": response.content,
                "score": 0.5
            }
    except Exception as e:
        print(f"ERROR: LLM Service failure: {e}")
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
