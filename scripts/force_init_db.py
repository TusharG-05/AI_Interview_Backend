import sys
import os

# Add parent dir to path
sys.path.append(os.getcwd())

from app.core.database import init_db

if __name__ == "__main__":
    print("Initializing Database...")
    init_db()
    print("Database Initialized.")
