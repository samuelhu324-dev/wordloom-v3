"""Upgrade books table timestamp columns to timestamptz handling dependent views.

Steps:
  1. Capture view definitions for active_books & basement_books if exist.
  2. Drop those views (they depend on soft_deleted_at / timestamps).
  3. ALTER columns soft_deleted_at, created_at, updated_at to timestamptz (UTC conversion).
  4. Recreate the views using their prior definitions (adapted if necessary) or sane defaults.
  5. Verify resulting data types.

Idempotent behavior:
  - If columns already timestamptz: prints and skips ALTER.
  - If views absent: proceeds with ALTER; then recreates defaults.

Safe conversion rule:
  USING col AT TIME ZONE 'UTC' converts naive timestamps (assumed UTC) to timestamptz preserving instant.

Usage (PowerShell):
    cd backend
    $env:DATABASE_URL="postgresql://postgres:pgpass@172.31.150.143:5432/wordloom"
    ..\\.venv\\Scripts\\python.exe scripts\\upgrade_books_timestamps_with_views.py
"""

from __future__ import annotations
import asyncio
import sys
from typing import Dict
from sqlalchemy import text
from infra.database.session import get_engine

TARGET_COLS = ["soft_deleted_at", "created_at", "updated_at"]
VIEW_NAMES = ["active_books", "basement_books"]

def windows_event_loop_patch():
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

FETCH_VIEWDEF_SQL = """
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_schema='public' AND table_name = ANY(:names)
"""

FETCH_COLUMNS_SQL = """
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema='public' AND table_name='books'
"""

ALTER_TEMPLATE = (
    "ALTER TABLE public.books ALTER COLUMN {col} TYPE timestamptz USING {col} AT TIME ZONE 'UTC';"
)

DEFAULT_VIEW_SQL: Dict[str, str] = {
    "active_books": "CREATE OR REPLACE VIEW public.active_books AS SELECT * FROM public.books WHERE soft_deleted_at IS NULL;",
    "basement_books": "CREATE OR REPLACE VIEW public.basement_books AS SELECT * FROM public.books WHERE soft_deleted_at IS NOT NULL ORDER BY soft_deleted_at DESC;",
}

async def upgrade():
    engine = await get_engine()
    async with engine.begin() as conn:
        # 1. Capture existing view definitions
        existing_defs: Dict[str, str] = {}
        # SQLAlchemy + psycopg parameter passing for ANY() expects a list/tuple; wrap as array
        res = await conn.execute(text(FETCH_VIEWDEF_SQL), {"names": VIEW_NAMES})
        for row in res.fetchall():
            name, definition = row
            existing_defs[name] = definition
        print("Found views:", ", ".join(existing_defs.keys()) or "<none>")

        # 2. Drop views if they exist
        for view in VIEW_NAMES:
            if view in existing_defs:
                stmt = f"DROP VIEW IF EXISTS public.{view} CASCADE;"
                print("Dropping view:", view)
                await conn.exec_driver_sql(stmt)
        if existing_defs:
            print("Views dropped.")

        # 3. ALTER columns
        cols_res = await conn.execute(text(FETCH_COLUMNS_SQL))
        types = {r[0]: r[1] for r in cols_res.fetchall()}
        print("Current column types:")
        for c in TARGET_COLS:
            print(f"  - {c}: {types.get(c, 'MISSING')}")

        to_alter = [c for c in TARGET_COLS if types.get(c) == "timestamp without time zone"]
        if not to_alter:
            print("No columns require ALTER.")
        else:
            for col in to_alter:
                stmt = ALTER_TEMPLATE.format(col=col)
                print("Altering column:", col)
                await conn.exec_driver_sql(stmt)
            print("ALTER complete.")

        # 4. Recreate views (use original definitions if captured, else defaults)
        for view in VIEW_NAMES:
            if view in existing_defs:
                # Original definition may come formatted; wrap in CREATE OR REPLACE VIEW
                # information_schema.view_definition returns the SELECT only.
                select_sql = existing_defs[view].rstrip(";")
                stmt = f"CREATE OR REPLACE VIEW public.{view} AS {select_sql};"
            else:
                stmt = DEFAULT_VIEW_SQL[view]
            print("Recreating view:", view)
            await conn.exec_driver_sql(stmt)
        print("Views recreated.")

        # 5. Verify
        verify_res = await conn.execute(text(FETCH_COLUMNS_SQL))
        verify_types = {r[0]: r[1] for r in verify_res.fetchall()}
        print("Post-upgrade types:")
        for c in TARGET_COLS:
            print(f"  - {c}: {verify_types.get(c)}")

    await engine.dispose()
    print("Upgrade script finished.")

def main():
    windows_event_loop_patch()
    asyncio.run(upgrade())

if __name__ == "__main__":
    main()
