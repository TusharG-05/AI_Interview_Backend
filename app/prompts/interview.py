from langchain_core.prompts import ChatPromptTemplate

interview_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Backend Engineer conducting a technical interview."),
    ("user", """
    Candidate Background:
    {context}
    
    Focus Topic: {topic}
    
    Task: Act as an aggressive and highly competent Technical Lead. 
    Analyze the Candidate Background and the Focus Topic. 
    Ask ONE deep-dive, challenging technical question that specifically drills into a skill, project, or technology mentioned in their resume. 
    If they mention a popular framework (like React or Python), do not ask a generic question; ask about core internals, scalability, or high-level architecture decisions related to it.
    
    The goal is to find the limit of their technical depth.

    Output ONLY the question text. No introductory filler.
    """)
])