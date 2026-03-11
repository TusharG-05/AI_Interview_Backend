import subprocess
import sys

with open("test_out.txt", "w", encoding="utf-8") as f:
    result = subprocess.run([sys.executable, "tests/api/comprehensive_test.py"], stdout=f, stderr=f)
    print("Test finished with exit code", result.returncode)
