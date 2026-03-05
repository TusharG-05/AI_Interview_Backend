#!/usr/bin/env python3
"""
backup_db.py — Export ALL current database data to a timestamped JSON file.

Usage:
    # Backup local Postgres (pre-migration):
    python scripts/backup_db.py

    # Backup a specific DB URL:
    DATABASE_URL="postgresql://user:pass@host/db" python scripts/backup_db.py

Output:
    backups/backup_YYYYMMDD_HHMMSS.json
"""
import os
import sys
import json
import base64
from datetime import datetime, date, timezone
from decimal import Decimal

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import sqlalchemy as sa

# ─── Database connection ──────────────────────────────────────────────────────
# Defaults to local Postgres (pre-migration DB)
LOCAL_DB_URL = os.getenv(
    "LOCAL_DATABASE_URL",
    "postgresql://postgres:Tush%234184@localhost:5432/interview_db"
)
DATABASE_URL = os.getenv("BACKUP_DATABASE_URL", LOCAL_DB_URL)

print(f"🔌 Connecting to: {DATABASE_URL.split('@')[-1]}")  # hide credentials

engine = sa.create_engine(DATABASE_URL)

# ─── Serialisation helpers ────────────────────────────────────────────────────
def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, memoryview):
        return base64.b64encode(bytes(obj)).decode("ascii")
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def dump_table(conn, table_name: str) -> list:
    """Fetch all rows from a table and return as a list of dicts."""
    try:
        result = conn.execute(sa.text(f'SELECT * FROM "{table_name}"'))
        columns = result.keys()
        rows = []
        for row in result:
            rows.append(dict(zip(columns, row)))
        return rows
    except Exception as e:
        print(f"  ⚠️  Skipping table '{table_name}': {e}")
        return []


def get_all_tables(conn) -> list:
    """Return all user-defined table names in the current schema."""
    result = conn.execute(sa.text(
        "SELECT tablename FROM pg_tables "
        "WHERE schemaname = 'public' ORDER BY tablename"
    ))
    return [row[0] for row in result]


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs("backups", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"backups/backup_{timestamp}.json"

    backup = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": DATABASE_URL.split("@")[-1],  # hide creds
            "tables": {}
        },
        "data": {}
    }

    with engine.connect() as conn:
        # Get current Alembic revision
        try:
            rev = conn.execute(sa.text(
                "SELECT version_num FROM alembic_version"
            )).fetchone()
            backup["metadata"]["alembic_revision"] = rev[0] if rev else "unknown"
        except Exception:
            backup["metadata"]["alembic_revision"] = "unknown"

        tables = get_all_tables(conn)
        print(f"\n📋 Found {len(tables)} tables: {', '.join(tables)}\n")

        for table in tables:
            if table == "alembic_version":
                continue  # skip meta table
            print(f"  📦 Backing up: {table}")
            rows = dump_table(conn, table)
            backup["data"][table] = rows
            backup["metadata"]["tables"][table] = len(rows)
            print(f"      → {len(rows)} rows")

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(backup, f, default=json_serializer, indent=2, ensure_ascii=False)

    total_rows = sum(backup["metadata"]["tables"].values())
    print(f"\n✅ Backup complete!")
    print(f"   File   : {output_path}")
    print(f"   Tables : {len(backup['metadata']['tables'])}")
    print(f"   Rows   : {total_rows}")
    print(f"   Alembic: {backup['metadata']['alembic_revision']}")
    print(f"\n⚠️  Keep this file safe — use restore_db.py to recover data if needed.")


if __name__ == "__main__":
    main()
