import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys

from dotenv import load_dotenv
import urllib.parse

load_dotenv()

def create_database():
    # Parse DATABASE_URL from .env
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_interview_db")
    try:
        url = urllib.parse.urlparse(database_url)
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port
        dbname = url.path[1:] 
    except Exception as e:
        print(f"Error parsing DATABASE_URL: {e}")
        return


    try:
        # Connect to default 'postgres' database
        con = psycopg2.connect(dbname="postgres", user=user, host=host, password=password, port=port)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database {dbname}...")
            cur.execute(f"CREATE DATABASE {dbname}")
            print("Database created successfully!")
        else:
            print(f"Database {dbname} already exists.")
            
        cur.close()
        con.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Please ensure PostgreSQL is running and credentials are correct (user:postgres, pass:password).")

if __name__ == "__main__":
    create_database()

