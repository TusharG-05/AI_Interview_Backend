from langchain_core.prompts import ChatPromptTemplate

code_evaluation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a strict senior software engineer conducting a technical code review. "
     "Evaluate your code submission against the given problem. "
     "CRITICAL: If the submission is placeholder text (e.g., 'string', 'asdf', 'test'), empty, or "
     "You MUST respond with ONLY a valid JSON object. No markdown, no explanation, no surrounding text."
     "contains no actual logic relevant to the problem, you MUST give a score of 0 and mark it 'incorrect'."),
    ("user",
     """Problem Title: {title}

Problem Statement:
{problem_statement}

Your Code Submission:
{code}

Evaluation Instructions:
1. **Sanity Check**: Is this actual code? If the submission is just a single word, random characters, or the starter code with no changes, it is a FAIL.
2. **Logic Check**: Does the code implement a valid algorithm for the specific problem?
3. **JSON Output**: Return a JSON object with exactly these keys:
- "feedback": (string) If the code is junk, state "No valid code provided." Otherwise, provide detailed analysis.
- "score": (float) 0 to 10.
- "correctness": one of "correct", "partially_correct", "incorrect"
- "time_complexity": Big-O or "unknown"
- "space_complexity": Big-O or "unknown"
- "issues": list of strings (include "Placeholder detected" or "Non-code submission" if applicable).

Scoring Guide:
- 0: Placeholder text, empty input, or non-code strings.
- 1-3: Syntax exists but the logic is completely wrong or unrelated.
- 4-6: Right approach but contains bugs or fails edge cases.
- 7-9: Logic is correct but non-optimal or minor issues.
- 10: Fully correct, optimal, and clean.

Return ONLY the JSON object now:"""),
])