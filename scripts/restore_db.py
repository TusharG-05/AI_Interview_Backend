#!/usr/bin/env python3
"""
restore_db.py — Restore data from a JSON backup after a migration.

Usage:
    # Restore to local Postgres (post-migration):
    python scripts/restore_db.py backups/backup_YYYYMMDD_HHMMSS.json

    # Dry-run (shows what would be inserted, no changes):
    python scripts/restore_db.py backups/backup_YYYYMMDD_HHMMSS.json --dry-run

IMPORTANT:
    - Run `alembic upgrade head` BEFORE restoring.
    - The script skips columns that no longer exist in the DB after migration.
    - Foreign key order: user → team → questionpaper → questions 
                         → interviewsession → answers → interviewresult
                         → proctoringevent
"""
import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import sqlalchemy as sa

# ─── Settings ─────────────────────────────────────────────────────────────────
LOCAL_DB_URL = os.getenv(
    "LOCAL_DATABASE_URL",
    "postgresql://postgres:Tush%234184@localhost:5432/interview_db"
)
RESTORE_DATABASE_URL = os.getenv("RESTORE_DATABASE_URL", LOCAL_DB_URL)

# Order matters — parent tables must come before child tables (FK dependencies)
TABLE_RESTORE_ORDER = [
    "user",
    "team",
    "questionpaper",
    "questions",
    "interviewsession",
    "answers",
    "interviewresult",
    "proctoringevent",
]


def get_existing_columns(conn, table_name: str) -> set:
    """Return the set of column names that currently exist in the DB table."""
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t"
    ), {"t": table_name})
    return {row[0] for row in result}


def restore_table(conn, table_name: str, rows: list, dry_run: bool) -> int:
    """Insert rows into table, skipping unknown columns. Returns inserted count."""
    if not rows:
        print(f"  ⏭️  {table_name}: 0 rows (empty backup)")
        return 0

    existing_cols = get_existing_columns(conn, table_name)
    if not existing_cols:
        print(f"  ⚠️  {table_name}: table not found in DB, skipping")
        return 0

    # Filter backup columns to only those that exist in current schema
    sample_cols = set(rows[0].keys())
    skipped_cols = sample_cols - existing_cols
    usable_cols = list(sample_cols & existing_cols)

    if skipped_cols:
        print(f"  ℹ️  {table_name}: skipping columns no longer in schema: {skipped_cols}")

    inserted = 0
    failed = 0
    for row in rows:
        filtered = {k: row[k] for k in usable_cols if k in row}
        if not filtered:
            continue

        if dry_run:
            inserted += 1
            continue

        try:
            cols = ", ".join(f'"{c}"' for c in filtered.keys())
            placeholders = ", ".join(f":{c}" for c in filtered.keys())
            stmt = sa.text(
                f'INSERT INTO "{table_name}" ({cols}) VALUES ({placeholders}) '
                f'ON CONFLICT DO NOTHING'
            )
            conn.execute(stmt, filtered)
            inserted += 1
        except Exception as e:
            failed += 1
            if failed <= 3:  # Only show first 3 errors per table
                print(f"  ⚠️  Row failed ({table_name}): {e}")

    return inserted


def main():
    parser = argparse.ArgumentParser(description="Restore database from JSON backup")
    parser.add_argument("backup_file", help="Path to backup JSON file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without making changes")
    args = parser.parse_args()

    if not os.path.exists(args.backup_file):
        print(f"❌ Backup file not found: {args.backup_file}")
        sys.exit(1)

    print(f"📂 Loading backup: {args.backup_file}")
    with open(args.backup_file, "r", encoding="utf-8") as f:
        backup = json.load(f)

    meta = backup.get("metadata", {})
    print(f"   Backup created : {meta.get('timestamp', 'unknown')}")
    print(f"   Alembic at time: {meta.get('alembic_revision', 'unknown')}")
    print(f"   Tables         : {list(meta.get('tables', {}).keys())}")
    print()

    if args.dry_run:
        print("🔍 DRY RUN — no changes will be made\n")

    engine = sa.create_engine(RESTORE_DATABASE_URL)
    print(f"🔌 Restoring to: {RESTORE_DATABASE_URL.split('@')[-1]}\n")

    # Check current alembic revision
    with engine.connect() as conn:
        try:
            rev = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchone()
            current_rev = rev[0] if rev else "unknown"
            print(f"   Current DB alembic: {current_rev}")
        except Exception:
            current_rev = "unknown"
            print("   ⚠️  Could not read alembic_version")

    data = backup.get("data", {})

    # Build restore order: prioritised tables first, then any extras
    restore_order = [t for t in TABLE_RESTORE_ORDER if t in data]
    extra_tables = [t for t in data if t not in TABLE_RESTORE_ORDER]
    restore_order.extend(extra_tables)

    total_inserted = 0

    with engine.begin() as conn:
        # Temporarily disable FK checks for restore
        conn.execute(sa.text("SET session_replication_role = replica"))

        for table in restore_order:
            rows = data.get(table, [])
            print(f"  📥 Restoring {table} ({len(rows)} rows)...")
            n = restore_table(conn, table, rows, args.dry_run)
            total_inserted += n
            print(f"      → {n} rows {'would be ' if args.dry_run else ''}inserted")

        if not args.dry_run:
            conn.execute(sa.text("SET session_replication_role = DEFAULT"))

    label = "Would insert" if args.dry_run else "Inserted"
    print(f"\n✅ Restore {'dry-run ' if args.dry_run else ''}complete!")
    print(f"   {label}: {total_inserted} total rows")
    if args.dry_run:
        print("\n   Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
