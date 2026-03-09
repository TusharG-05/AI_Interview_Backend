"""Start uvicorn and redirect all output to a proper UTF-8 log file."""
import subprocess, sys

with open("server.log", "w", encoding="utf-8", buffering=1) as log:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.server:app",
         "--host", "0.0.0.0", "--port", "8001", "--log-level", "debug"],
        stdout=log, stderr=log
    )
    proc.wait()
