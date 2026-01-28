import random
import json
from typing import Dict, Union, Optional
from sqlmodel import Session, select
from models.db_models import Question
from config.settings import local_llm
from prompts.interview import interview_prompt
from prompts.evaluation import evaluation_prompt

# Constants
RESUME_TOPICS = ["Data Structures & Algorithms", "System Design", "Database Management", "API Design", "Security", "Scalability", "DevOps"]

# Chains
interview_chain = interview_prompt | local_llm
evaluation_chain = evaluation_prompt | local_llm

def generate_resume_question_content(context: str, resume_text: str) -> dict:
    random_topic = random.choice(RESUME_TOPICS)
    full_context = f"User Provided Context: {context}\n\nResume Content: {resume_text}"
    
    response = interview_chain.invoke({
        "context": full_context,
        "topic": random_topic
    })
    
    return {
        "question": response.content,
        "topic": random_topic
    }

def evaluate_answer_content(question: str, answer: str) -> Dict[str, Union[str, float]]:
    response = evaluation_chain.invoke({
        "question": question,
        "answer": answer
    })
    
    try:
        # Attempt to parse JSON from the LLM response
        result = json.loads(response.content)
        # Ensure keys exist
        if "feedback" not in result:
             result["feedback"] = str(response.content)
        if "score" not in result:
             result["score"] = 0.0
        return result
    except json.JSONDecodeError:
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
        session.commit()
        session.refresh(question)
        
    return question

def get_custom_response(prompt: str) -> str:
    response = local_llm.invoke(prompt)
    return response.content
