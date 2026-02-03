import random
import json
from typing import Dict, Union, Optional
from sqlmodel import Session, select
from ..models.db_models import Question
from ..core.config import local_llm
from ..prompts.interview import interview_prompt
from ..prompts.evaluation import evaluation_prompt

# Constants
RESUME_TOPICS = ["Data Structures & Algorithms", "System Design", "Database Management", "API Design", "Security", "Scalability", "DevOps"]

# Chains
interview_chain = interview_prompt | local_llm 
evaluation_chain = evaluation_prompt | local_llm

def generate_resume_question_content(context: str, resume_text: str) -> dict:
    # Use a priority sub-set of topics if they appear in resume
    keywords = ["React", "Python", "Kubernetes", "Docker", "Go", "AWS", "SQL", "NoSQL", "Redis"]
    found_keywords = [k for k in keywords if k.lower() in resume_text.lower()]
    
    selected_topic = random.choice(found_keywords) if found_keywords else random.choice(RESUME_TOPICS)
    
    full_context = f"User Intent: {context}\n\nTECHNICAL RESUME DATA:\n{resume_text}"
    
    # We use the updated 'aggressive' prompt in the chain
    response = interview_chain.invoke({
        "context": full_context,
        "topic": selected_topic
    })
    
    return {
        "question": response.content,
        "topic": selected_topic
    }

def evaluate_answer_content(question: str, answer: str) -> Dict[str, Union[str, float]]:
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
             result["score"] = 0.0
             
        print(f"DEBUG: Parsed Score: {result['score']}")
        return result
    except json.JSONDecodeError:
        print("DEBUG: JSON parsing failed, returning fallback result.")
        # Fallback if LLM fails to return valid JSON
        return {
            "feedback": response.content,
            "score": 0.0
        }

def get_or_create_question(session: Session, content: str, topic: str = "General", difficulty: str = "Unknown") -> Question:
    """Finds a question by content or creates a new one."""
    stmt = select(Question).where(Question.content == content)
    question = session.exec(stmt).first()
    
    if not question:
        question = Question(content=content, topic=topic, difficulty=difficulty)
        session.add(question)
        session.flush() # Get ID but don't commit yet
        session.refresh(question)
        
    return question

def get_custom_response(prompt: str) -> str:
    response = local_llm.invoke(prompt)
    return response.content
