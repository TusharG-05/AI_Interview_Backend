from langchain_core.prompts import ChatPromptTemplate

code_evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior software engineer conducting a technical coding interview. "
     "Evaluate the candidate's code submission against the given problem. "
     "You MUST respond with ONLY a valid JSON object. No markdown, no explanation, no surrounding text."),
    ("user",
     """Problem Title: {title}

Problem Statement:
{problem_statement}

Candidate's Code Submission:
{code}

Evaluate the code submission and return a JSON object with exactly these keys:
- "feedback": detailed feedback string (what was done well, what was wrong, how to improve)
- "score": float between 0 and 10
- "correctness": one of "correct", "partially_correct", "incorrect"
- "time_complexity": estimated Big-O time complexity (e.g. "O(n)", "O(n log n)") or "unknown"
- "space_complexity": estimated Big-O space complexity or "unknown"
- "issues": list of strings describing specific bugs or problems found (empty list if none)

Scoring guide:
- 0-3: Incorrect approach, major logical errors, or empty submission
- 4-6: Partially correct, right approach but bugs or edge cases missed
- 7-9: Correct with minor issues (e.g. non-optimal complexity)
- 10: Fully correct, optimal, clean code

Return ONLY the JSON object now:"""),
])
