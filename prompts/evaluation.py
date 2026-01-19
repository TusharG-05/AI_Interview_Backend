"""Answer evaluation and feedback prompts."""

from langchain_core.prompts import ChatPromptTemplate

# Answer Evaluation Prompt
evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer. Provide constructive feedback on the candidate's answer."),
    ("user", "Question: {question}\n\nCandidate's Answer: {answer}\n\nProvide feedback on their answer including strengths and areas for improvement.")
])
