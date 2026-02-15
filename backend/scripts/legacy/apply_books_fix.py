"""Apply missing columns fix for books table.

Problem: Runtime queries reference columns is_pinned, block_count, due_at
which may be absent in existing databases created from earlier schema
version (001_create_core_schema.sql) that lacked these columns.

This script:
1. Adds columns if missing (is_pinned, block_count, due_at)
2. Normalizes status values to lowercase
3. Ensures default status is 'draft'
4. Prints resulting column list for verification

Safe to run multiple times: all ALTER statements use IF NOT EXISTS semantics
or are idempotent updates.
"""

import asyncio
import pathlib
import sys
from sqlalchemy import text

# Ensure backend directory is on path so 'infra' becomes top-level
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from infra.database.session import get_engine

DDL_STATEMENTS = [
    # Add columns (IF NOT EXISTS supported by Postgres 9.6+ for ADD COLUMN)
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE;",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS block_count INT NOT NULL DEFAULT 0;",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS due_at TIMESTAMPTZ NULL;",
    # Normalize status values
    "UPDATE books SET status = LOWER(status) WHERE status <> LOWER(status);",
    # Set default to 'draft'
    "ALTER TABLE books ALTER COLUMN status SET DEFAULT 'draft';",
]

VERIFY_QUERY = text("""
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name='books'
ORDER BY ordinal_position;
""")

async def apply_fix():
    engine = await get_engine()
    async with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            await conn.exec_driver_sql(stmt)
        result = await conn.execute(VERIFY_QUERY)
        cols = [f"{r.column_name}:{r.data_type}" for r in result]
        print("[OK] books columns ->", ", ".join(cols))
    await engine.dispose()

if __name__ == "__main__":
    import selectors
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)
    loop.run_until_complete(apply_fix())
    loop.close()
