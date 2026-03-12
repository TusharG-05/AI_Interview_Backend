from langchain_core.prompts import ChatPromptTemplate

# Answer Evaluation Prompt
evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer. Provide constructive feedback on your own response."),
    ("system", "Evaluate the answer provided in the previous turn."),
    ("user", "You must return your response in a valid JSON format with exactly two keys: 'feedback' (string) and 'score' (float between 0 and 10)."),
    ("user", "Question: {question}\n\nYour Answer: {answer}"),
    ("user", "Do not include any text outside the JSON object.")
])