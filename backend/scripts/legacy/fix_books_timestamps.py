"""Fix books table timestamp columns to timestamptz (UTC).

Columns targeted (if currently timestamp without time zone):
  - soft_deleted_at
  - created_at
  - updated_at

Conversion uses AT TIME ZONE 'UTC' to preserve original naive values as UTC.

Idempotent: skips columns already timestamptz.

Usage (PowerShell):
  cd backend
    $env:DATABASE_URL="postgresql://postgres:pgpass@172.31.150.143:5434/wordloom"
  ..\.venv\Scripts\python.exe scripts\fix_books_timestamps.py
"""

from __future__ import annotations
import asyncio
import sys
from sqlalchemy import text
from infra.database.session import get_engine

TARGET = ["soft_deleted_at", "created_at", "updated_at"]

QUERY_COLUMNS = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema='public' AND table_name='books'
"""

ALTER_TEMPLATE = (
    "ALTER TABLE public.books ALTER COLUMN {col} TYPE timestamptz "
    "USING {col} AT TIME ZONE 'UTC';"
)


async def run_fix():
    engine = await get_engine()
    async with engine.begin() as conn:
        res = await conn.execute(text(QUERY_COLUMNS))
        current = {r[0]: r[1] for r in res.fetchall()}

        to_fix = [c for c in TARGET if current.get(c) == "timestamp without time zone"]
        already_ok = [c for c in TARGET if current.get(c) == "timestamp with time zone"]
        missing = [c for c in TARGET if c not in current]

        print("Books table columns:")
        for k in TARGET:
            print(f"  - {k}: {current.get(k, 'MISSING')}")

        if missing:
            print(f"\n⚠️ Missing expected columns (skip): {', '.join(missing)}")
        if already_ok:
            print(f"\n✅ Already timestamptz: {', '.join(already_ok)}")
        if not to_fix:
            print("\nNothing to fix.")
        else:
            print(f"\nWill fix columns: {', '.join(to_fix)}")
            for col in to_fix:
                stmt = ALTER_TEMPLATE.format(col=col)
                print("Executing: " + stmt)
                await conn.exec_driver_sql(stmt)
            print("\n✅ Conversion complete.")

    await engine.dispose()


def main():
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(run_fix())


if __name__ == "__main__":
    main()
