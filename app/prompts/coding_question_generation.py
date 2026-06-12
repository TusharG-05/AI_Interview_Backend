from langchain_core.prompts import ChatPromptTemplate

coding_question_generation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior software engineer, competitive programming expert, and strict parser. "
     "You MUST respond with ONLY a valid JSON array. No markdown, no explanation, no surrounding text."),
    ("user",
     """You have been provided with a topic, job description, OR an explicit coding problem definition.

Input: {ai_prompt}
Difficulty Mix: {difficulty_mix}
Requested Number of Questions: {num_questions}

Rules:
1. VERBATIM PRESERVATION: IF the input contains a specific coding problem (e.g., specific function to fix, specific rules like 'no for loops', or exact starter code), you MUST preserve the exact problem statement, rules, and starter code provided in the input without rewriting them into a generic LeetCode format.
2. IF the input is just a general topic (like "Arrays"), generate {num_questions} language-agnostic algorithmic challenges (like LeetCode).
3. If the input has fewer problems than requested, generate additional relevant ones to meet the exact `{num_questions}` total.
4. Difficulty mix: "easy" = all Easy, "medium" = all Medium, "hard" = all Hard, "mixed" = spread across Easy/Medium/Hard.
5. Examples must have at least 2 test cases with explanations.
6. Marks: Easy=10, Medium=15, Hard=20.

Return ONLY a JSON array with exactly {num_questions} objects. Each object must have these keys:
- "title": short problem name
- "problem_statement": full problem description with all context needed to solve it (preserve exact user wording if provided)
- "examples": array of objects, each with "input" (string), "output" (string), "explanation" (string)
- "constraints": array of constraint strings
- "starter_code": function signature + docstring hint (preserve exact provided user code if given)
- "topic": tag (e.g. "Arrays", "Dynamic Programming", "Debugging")
- "difficulty": one of "Easy", "Medium", "Hard"
- "marks": integer (Easy=10, Medium=15, Hard=20)
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
    "marks": 10,
    "response_type": "code"
  }}
]

Return ONLY the JSON array now:"""),
])
