from langchain_core.prompts import ChatPromptTemplate

# Answer Evaluation Prompt
evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer. Provide constructive feedback on the candidate's answer."),
    ("system", "Evaluate the answer given by the candidate.")
    ("user", "Use points out of 10 system for each question."),
    ("user", "Question: {question}\n\nCandidate's Answer: {answer}"),
    ("user", "Give feedback in bullet points."),
    ("user", "Do not include any additional information."),
])
