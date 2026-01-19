"""Interview question generation prompts."""

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
