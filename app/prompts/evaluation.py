from langchain_core.prompts import ChatPromptTemplate

# Answer Evaluation Prompt
evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert technical interviewer. Provide constructive feedback on the candidate's answer."),
    ("system", "Evaluate the answer given by the candidate. Use 'You' and 'Your' instead of 'the candidate' and 'the candidate's' in your feedback."),
    ("user", "You must return your response in a valid JSON format with exactly two keys: 'feedback' (string) and 'score_out_of_10' (float between 0 and 10)."),
    ("user", "Question: {question}\n\nYour Answer: {answer}"),
    ("user", "Do not include any text outside the JSON object."),
])
