import subprocess

with open("clean_test_output.log", "w", encoding="utf-8") as f:
    subprocess.run([".\\.venv\\Scripts\\python", "tests/api/comprehensive_test.py"], stdout=f, stderr=f)
