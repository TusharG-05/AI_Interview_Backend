from langchain_core.prompts import ChatPromptTemplate

interview_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Backend Engineer conducting a technical interview."),
    ("user", """
    Candidate Background:
    {context}
    
    Focus Topic: {topic}
    
    Task: Ask ONE challenging technical question related to the Focus Topic. 
    If a resume is provided, try to link the question to their experience.
    
    Output ONLY the question text. No introductory filler.
    """)
])