from langchain_core.prompts import ChatPromptTemplate

# Question Generation Prompt
question_generation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert technical interviewer and parser. "
     "You MUST respond with ONLY a valid JSON array. No markdown, no explanation, no surrounding text."),
    ("user",
     """You have been provided with a topic, job description, OR a list of explicit questions.

Input: {ai_prompt}
Years of Experience: {years_of_experience}
Requested Number of Questions: {num_questions}

Rules:
1. VERBATIM EXTRACTION: IF the input contains a list of specific questions, you MUST extract and format them exactly as written. Do not alter their core meaning, summarize, or drop them.
2. PRESERVE OPTIONS: IF a question contains multiple-choice options (e.g., A, B, C, D), you MUST include all the options verbatim inside the "question_text" string. DO NOT strip them out.
3. If the input has fewer questions than requested, generate additional relevant ones to meet the exact `{num_questions}` total.
4. IF the input is just a topic or job description, generate {num_questions} interview questions tailored to the experience level.
5. Tailor difficulty to the experience level (junior 0-2 yrs = Easy/Medium, mid 3-5 yrs = Medium, senior 6+ yrs = Medium/Hard).
6. Each question must be answerable verbally in an interview setting (if it has options, they will just verbally say the option).

Return ONLY a JSON array with exactly {num_questions} objects. Each object must have these keys:
- "question_text": the full question string
- "topic": short topic tag (e.g. "Python", "System Design", "Databases")
- "difficulty": one of "Easy", "Medium", "Hard"
- "marks": integer based on difficulty (Easy=1, Medium=3, Hard=5)
- "response_type": always "text"

Example format (do not copy this content, just the structure):
[
  {{"question_text": "Explain the GIL in Python.", "topic": "Python", "difficulty": "Medium", "marks": 3, "response_type": "text"}},
  {{"question_text": "Design a URL shortener.", "topic": "System Design", "difficulty": "Hard", "marks": 5, "response_type": "text"}}
]

Return ONLY the JSON array now:"""),
])
