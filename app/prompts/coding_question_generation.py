from langchain_core.prompts import ChatPromptTemplate

coding_question_generation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior software engineer and competitive programming expert who creates LeetCode-style coding problems. "
     "You MUST respond with ONLY a valid JSON array. No markdown, no explanation, no surrounding text."),
    ("user",
     """Generate exactly {num_questions} coding interview problem(s) on the following topic.

Topic: {ai_prompt}
Difficulty Mix: {difficulty_mix}

Rules:
- Problems must be language-agnostic algorithmic challenges (like LeetCode).
- Difficulty mix: "easy" = all Easy, "medium" = all Medium, "hard" = all Hard, "mixed" = spread across Easy/Medium/Hard.
- Each problem must be self-contained and solvable without extra context.
- Starter code must use generic pseudocode-style function signatures (no language-specific imports).
- Examples must have at least 2 test cases with explanations.
- Marks: Easy=3, Medium=6, Hard=10.

Return ONLY a JSON array with exactly {num_questions} objects. Each object must have these keys:
- "title": short problem name (e.g. "Two Sum", "Valid Parentheses")
- "problem_statement": full problem description with all context needed to solve it
- "examples": array of objects, each with "input" (string), "output" (string), "explanation" (string)
- "constraints": array of constraint strings (e.g. ["1 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"])
- "starter_code": language-agnostic function signature + docstring hint (e.g. "function twoSum(nums, target):\\n    # Return indices of two numbers that add up to target\\n    pass")
- "topic": tag (e.g. "Arrays", "Dynamic Programming", "Graphs", "Binary Search")
- "difficulty": one of "Easy", "Medium", "Hard"
- "marks": integer (Easy=3, Medium=6, Hard=10)
- "response_type": always "code"

Example format (do not copy this content, just the structure):
[
  {{
    "title": "Two Sum",
    "problem_statement": "Given an array of integers nums and an integer target, return indices of two numbers that add up to target. You may assume exactly one solution exists.",
    "examples": [
      {{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"}}
    ],
    "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
    "starter_code": "function twoSum(nums, target):\\n    # Return list of two indices\\n    pass",
    "topic": "Arrays",
    "difficulty": "Easy",
    "marks": 3,
    "response_type": "code"
  }}
]

Return ONLY the JSON array now:"""),
])
