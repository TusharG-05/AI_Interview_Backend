import os

ROUTER_PATH = "app/routers/admin.py"
RESPONSES_PATH = "app/schemas/responses.py"
RESULT_PATH = "app/schemas/interview_result.py"

with open(ROUTER_PATH, "r") as f:
    rcontent = f.read()

# targeted replaces
rcontent = rcontent.replace("QuestionPaper.admin_id", "QuestionPaper.adminUser")
rcontent = rcontent.replace("paper.admin_id", "paper.adminUser")

with open(ROUTER_PATH, "w") as f:
    f.write(rcontent)

# We also need to check the schemas to see if they need adminUser
def replace_in_file(filepath, old, new):
    if not os.path.exists(filepath): return
    with open(filepath, "r") as f:
        c = f.read()
    c = c.replace(old, new)
    with open(filepath, "w") as f:
        f.write(c)

replace_in_file(RESPONSES_PATH, "class QuestionPaperRead(BaseModel):\n    id: int\n    name: str\n    description: Optional[str] = None\n    admin_id: Optional[int] = None", "class QuestionPaperRead(BaseModel):\n    id: int\n    name: str\n    description: str = \"\"\n    adminUser: Optional[int] = None\n    question_count: int = 0\n    total_marks: int = 0")

replace_in_file(RESULT_PATH, "class QuestionPaperNested(BaseModel):\n    id: int\n    name: str\n    description: Optional[str] = None\n    admin_id: Optional[int] = None", "class QuestionPaperNested(BaseModel):\n    id: int\n    name: str\n    description: str = \"\"\n    adminUser: Optional[int] = None\n    question_count: int = 0\n    total_marks: int = 0")

print("Done")
