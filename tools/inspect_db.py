from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
if not url:
    print("DATABASE_URL not found")
    exit(1)

# Ensure the URL is valid for sqlalchemy (replace postgres:// with postgresql://)
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

print(f"Connecting to Database...")
print(f"URL: {url}")

try:
    engine = create_engine(url)
    insp = inspect(engine)
    tables = insp.get_table_names()
    print(f"\nFound {len(tables)} tables:")
    print(tables)
    print("="*30)

    with engine.connect() as conn:
        for table in tables:
            print(f"\n[ Table: {table} ]")
            try:
                # Count rows
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"Total Rows: {count}")
                
                if count > 0:
                    print("First 5 rows:")
                    result = conn.execute(text(f"SELECT * FROM {table} LIMIT 5"))
                    keys = list(result.keys())
                    print(f"Columns: {keys}")
                    for row in result:
                        print(row)
                else:
                    print("(Table is empty)")
            except Exception as e:
                print(f"Error reading table {table}: {e}")
            print("-" * 20)

except Exception as e:
    print(f"\nConnection Failed: {e}")
    print("\nEnsure PostgreSQL is running on localhost:5432 and credentials are correct.")
