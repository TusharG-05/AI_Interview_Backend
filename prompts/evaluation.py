from langchain_core.prompts import ChatPromptTemplate

# Answer Evaluation Prompt
evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer. Provide constructive feedback on the candidate's answer."),
    ("system", "Evaluate the answer given by the candidate."),
    ("user", "You must return your response in a valid JSON format with exactly two keys: 'feedback' (string) and 'score' (float between 0 and 10)."),
    ("user", "Question: {question}\n\nCandidate's Answer: {answer}"),
    ("user", "Do not include any text outside the JSON object."),
])

# Follow-up Question Prompt
followup_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer."),
    ("user", "Based on the candidate's previous answer, generate ONE short, relevant follow-up question to probe deeper or clarify their understanding."),
    ("user", "Original Question: {question}\nCandidate's Answer: {answer}"),
    ("user", "Output ONLY the follow-up question text.")
])
