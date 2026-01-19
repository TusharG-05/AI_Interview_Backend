"""
Prompts configuration for the AI Interview platform.
Modify these prompts to customize the interview behavior.
"""

from langchain_core.prompts import ChatPromptTemplate

# Interview Question Generation Prompt
interview_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Backend Engineer at a top tech company. "
               "Your goal is to conduct a mock interview. "
               "Be professional, technical, and slightly challenging. "
               "Ask questions in points for better clarity. "
               "Ask only one question."),
    ("user", "Based on this candidate's resume snippet: {context}, "
             "generate one deep-dive technical question about {topic}.")
])

# Answer Evaluation Prompt
evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer. Provide constructive feedback on the candidate's answer."),
    ("user", "Question: {question}\n\nCandidate's Answer: {answer}\n\nProvide feedback on their answer including strengths and areas for improvement.")
])
