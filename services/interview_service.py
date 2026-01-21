import random
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

def evaluate_answer_content(question: str, answer: str) -> str:
    response = evaluation_chain.invoke({
        "question": question,
        "answer": answer
    })
    return response.content

def get_custom_response(prompt: str) -> str:
    response = local_llm.invoke(prompt)
    return response.content
