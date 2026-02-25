
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL')
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT id, access_token FROM interviewsession ORDER BY id DESC LIMIT 5')).fetchall()
    print("Recent Interview Sessions:")
    for row in result:
        print(f"ID: {row[0]}, Token: {row[1]}")
