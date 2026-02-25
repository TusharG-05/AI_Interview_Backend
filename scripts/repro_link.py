
import os
import uuid
from dotenv import load_dotenv

# Mocking the environment/config
load_dotenv()
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
access_token = uuid.uuid4().hex

link = f"{APP_BASE_URL}/interview/{access_token}"

print(f"Generated Link: {link}")
print(f"Access Token: {access_token}")
