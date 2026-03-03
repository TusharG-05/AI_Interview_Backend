from langchain_core.prompts import ChatPromptTemplate

# Question Generation Prompt
question_generation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert technical interviewer who creates high-quality interview question papers. "
     "You MUST respond with ONLY a valid JSON array. No markdown, no explanation, no surrounding text."),
    ("user",
     """Generate exactly {num_questions} interview questions for the following role/topic.

Topic / Job Description: {ai_prompt}
Years of Experience Required: {years_of_experience}

Rules:
- Tailor difficulty to the experience level (junior 0-2 yrs = Easy/Medium, mid 3-5 yrs = Medium, senior 6+ yrs = Medium/Hard).
- Vary topics and difficulty across the set.
- Each question must be answerable verbally in an interview setting.

Return ONLY a JSON array with exactly {num_questions} objects. Each object must have these keys:
- "question_text": the full question string
- "topic": short topic tag (e.g. "Python", "System Design", "Databases")
- "difficulty": one of "Easy", "Medium", "Hard"
- "marks": integer 1-10 based on difficulty (Easy=1-3, Medium=4-6, Hard=7-10)
- "response_type": always "text"

Example format (do not copy this content, just the structure):
[
  {{"question_text": "Explain the GIL in Python.", "topic": "Python", "difficulty": "Medium", "marks": 5, "response_type": "text"}},
  {{"question_text": "Design a URL shortener.", "topic": "System Design", "difficulty": "Hard", "marks": 8, "response_type": "text"}}
]

Return ONLY the JSON array now:"""),
])
