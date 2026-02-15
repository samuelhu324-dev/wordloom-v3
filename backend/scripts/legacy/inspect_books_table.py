"""Inspect and optionally migrate `books` table columns to match ORM definition.

Usage (PowerShell):
  cd backend
  ..\.venv\Scripts\python.exe scripts\inspect_books_table.py          # Just report
  ..\.venv\Scripts\python.exe scripts\inspect_books_table.py --apply   # Apply missing columns

Safe Behavior:
  - Reads current columns from information_schema
  - Compares with expected set from ORM (hard-coded list to avoid import side-effects)
  - Prints SQL ALTER statements required
  - Only executes them when --apply flag provided

Idempotent: Re-running after success should show no missing columns.
"""

from __future__ import annotations
import asyncio
import argparse
import sys
from typing import List
from sqlalchemy import text
from infra.database.session import get_engine

EXPECTED_COLUMNS = {
    "id": "uuid",
    "bookshelf_id": "uuid",
    "library_id": "uuid",
    "title": "character varying",
    "summary": "text",
    "is_pinned": "boolean",
    "due_at": "timestamp with time zone",
    "status": "character varying",
    "block_count": "integer",
    "soft_deleted_at": "timestamp with time zone",
    "created_at": "timestamp with time zone",
    "updated_at": "timestamp with time zone",
}


def build_alter(column: str) -> str:
    # Minimal column definitions aligned with ORM (constraints like FK must be handled separately)
    mapping = {
        "id": "ADD COLUMN id uuid DEFAULT gen_random_uuid() PRIMARY KEY",  # prefer extension uuid-ossp/gen_random_uuid()
        "bookshelf_id": "ADD COLUMN bookshelf_id uuid",
        "library_id": "ADD COLUMN library_id uuid",
        "title": "ADD COLUMN title varchar(255) NOT NULL DEFAULT ''",
        "summary": "ADD COLUMN summary text",
        "is_pinned": "ADD COLUMN is_pinned boolean NOT NULL DEFAULT false",
        "due_at": "ADD COLUMN due_at timestamptz",
        "status": "ADD COLUMN status varchar(50) NOT NULL DEFAULT 'draft'",
        "block_count": "ADD COLUMN block_count integer NOT NULL DEFAULT 0",
        "soft_deleted_at": "ADD COLUMN soft_deleted_at timestamptz",
        "created_at": "ADD COLUMN created_at timestamptz NOT NULL DEFAULT now()",
        "updated_at": "ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now()",
    }
    return f"ALTER TABLE public.books {mapping[column]};"


async def inspect(apply: bool):
    engine = await get_engine()
    async with engine.begin() as conn:
        result = await conn.execute(text(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name='books'
            ORDER BY ordinal_position
            """
        ))
        existing = {row[0]: row[1] for row in result.fetchall()}

    missing = [c for c in EXPECTED_COLUMNS.keys() if c not in existing]
    mismatched_types = [
        (c, existing.get(c), EXPECTED_COLUMNS[c])
        for c in EXPECTED_COLUMNS.keys()
        if c in existing and existing.get(c) != EXPECTED_COLUMNS[c]
    ]

    print("Current columns ({}):".format(len(existing)))
    for k, v in existing.items():
        print(f"  - {k}: {v}")

    if not existing:
        print("⚠️ Table 'books' does not exist. You must create it via migration.")
        return

    if missing:
        print("\nMissing columns ({}): {}".format(len(missing), ", ".join(missing)))
    else:
        print("\n✅ No missing columns.")

    if mismatched_types:
        print("\nType mismatches ({}):".format(len(mismatched_types)))
        for col, have, expect in mismatched_types:
            print(f"  - {col}: have '{have}' expect '{expect}'")
    else:
        print("\n✅ No type mismatches.")

    alters: List[str] = [build_alter(c) for c in missing]
    if alters:
        print("\nProposed ALTER statements:")
        for stmt in alters:
            print("  " + stmt)
    else:
        print("\nNo ALTER statements needed.")

    if apply and alters:
        print("\nApplying missing column ALTER statements...")
        async with engine.begin() as conn:
            for stmt in alters:
                await conn.exec_driver_sql(stmt)
        print("✅ Applied. Re-run script to verify.")
    elif apply and not alters:
        print("✅ Nothing to apply.")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Inspect and optionally migrate books table columns")
    parser.add_argument("--apply", action="store_true", help="Execute ALTER statements for missing columns")
    args = parser.parse_args()
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(inspect(apply=args.apply))


if __name__ == "__main__":
    main()
