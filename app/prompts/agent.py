from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

app = FastAPI()

"""
Initialize the local model via Ollama. 
Ensure you have run 'ollama run llama3' in your terminal.
"""
llm = OllamaLLM(model="llama3")

agent_question_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a professional AI Interviewer. Your sole task is to ask the next question from a provided list while maintaining a warm, conversational tone. "
        "STRICT OPERATIONAL RULES: "
        "1. Direct Progress: You must ONLY ask the question provided in the next_question variable. Do not invent new questions or ask for more details on previous answers. "
        "2. The Bridge: Briefly acknowledge the candidate's last response before transitioning. "
        "3. One at a Time: Ask exactly ONE question. Never bundle multiple questions into one response. "
        "4. No Feedback: Do not tell the candidate if their answer was right or wrong. "
        "5. Clean Output: Output ONLY the spoken dialogue. No labels, no meta-commentary, and no intro/outro text."
    ),
    (
        "user",
        "CONVERSATION LOG: \n{history}\n\nNEXT QUESTION TO ASK: \n{next_question}\n\nYour response:"
    ),
])

class InterviewRequest(BaseModel):
    history: str
    next_question: str

@app.post("/interviewer/next")
async def get_next_question(data: InterviewRequest):
    """
    This endpoint takes the chat history and the next question 
    string, then formats them into the prompt for Ollama.
    """
    chain = agent_question_prompt | llm
    
    response = chain.invoke({
        "history": data.history,
        "next_question": data.next_question
    })
    
    return {"message": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)