from pydantic import BaseModel

class QuestionRequest(BaseModel):
    """Request model for generating interview questions."""
    context: str
    topic: str

class AnswerRequest(BaseModel):
    """Request model for evaluating candidate answers."""
    question: str
    answer: str

class CustomPromptRequest(BaseModel):
    """Request model for custom prompts."""
    prompt: str

class EvaluateRequest(BaseModel):
    question: str
    answer: str
