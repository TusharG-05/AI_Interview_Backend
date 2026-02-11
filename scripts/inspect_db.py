import sys
import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Ensure we can import from the app directory
sys.path.append(os.getcwd())
load_dotenv()

def inspect_database():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Error: DATABASE_URL not found in environment variables.")
        return

    # Standard fix for deprecated postgres:// prefix
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    print(f"\nConnecting to: {url}")

    try:
        engine = create_engine(url)
        insp = inspect(engine)
        tables = insp.get_table_names()
        
        if not tables:
            print("Connected successfully, but no tables found in the database.")
            return

        print(f"\nFound {len(tables)} tables: {', '.join(tables)}")
        print("="*60)

        with engine.connect() as conn:
            for table in tables:
                print(f"\n[ Table: {table.upper()} ]")
                try:
                    # Count rows
                    count = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\"")).scalar()
                    print(f"Total Rows: {count}")
                    
                    if count > 0:
                        print("Sample Data (First 3 rows):")
                        result = conn.execute(text(f"SELECT * FROM \"{table}\" LIMIT 3"))
                        keys = list(result.keys())
                        print(f"Columns: {keys}")
                        for row in result:
                            # Truncate long strings for cleaner output
                            formatted_row = [str(val)[:50] + "..." if isinstance(val, str) and len(str(val)) > 50 else val for val in row]
                            print(formatted_row)
                    else:
                        print("(Table is empty)")
                except Exception as e:
                    print(f"Error reading table '{table}': {e}")
                print("-" * 30)
        print("\nDatabase inspection complete.\n")

    except Exception as e:
        print(f"\nConnection Failed: {e}")
        print("\nEnsure the database is running and credentials are correct.")

if __name__ == "__main__":
    inspect_database()
