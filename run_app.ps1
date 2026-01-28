$env:Path = "$PSScriptRoot\.venv311\Scripts;$env:Path"
python -m uvicorn main:app --reload
