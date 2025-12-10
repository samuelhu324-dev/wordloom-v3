"""Backfill basement bookshelf references for libraries.

This script makes sure every library row has a `basement_bookshelf_id` that points
at an actual Basement bookshelf belonging to the same library. It performs the
following steps:

1. Adds the `basement_bookshelf_id` column (and FK) if they are missing.
2. Finds libraries with NULL or invalid basement references.
3. Reuses an existing basement bookshelf when possible, otherwise creates a new
   hidden bookshelf named "Basement" for that library.
4. Updates the library row to point to the resolved bookshelf ID.

The script is idempotent and safe to run multiple times.
"""

import asyncio
import pathlib
import selectors
import sys
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

# Ensure backend directory is importable so we can reuse the shared DB helpers
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from infra.database.session import get_engine  # noqa: E402  (lazy import after sys.path)

ADD_COLUMN_SQL = """\
ALTER TABLE libraries
ADD COLUMN IF NOT EXISTS basement_bookshelf_id UUID NULL;
"""

CHECK_CONSTRAINT_SQL = text(
    """\
SELECT 1
FROM information_schema.table_constraints
WHERE table_name = 'libraries'
  AND constraint_name = 'libraries_basement_bookshelf_id_fkey';
"""
)

ADD_CONSTRAINT_SQL = """\
ALTER TABLE libraries
ADD CONSTRAINT libraries_basement_bookshelf_id_fkey
FOREIGN KEY (basement_bookshelf_id)
REFERENCES bookshelves (id)
ON DELETE SET NULL;
"""

UPSERT_BASEMENT_TRIGGER_SQL = """\
CREATE OR REPLACE FUNCTION create_library_basement()
RETURNS TRIGGER AS $$
DECLARE
    resolved_basement_id UUID;
BEGIN
    IF NEW.basement_bookshelf_id IS NULL THEN
        resolved_basement_id := gen_random_uuid();
        NEW.basement_bookshelf_id := resolved_basement_id;
    ELSE
        resolved_basement_id := NEW.basement_bookshelf_id;
    END IF;

    INSERT INTO bookshelves (id, library_id, name, is_basement, status)
    VALUES (resolved_basement_id, NEW.id, 'Basement', TRUE, 'active')
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

MISSING_OR_INVALID_LIBRARIES_SQL = text(
    """\
WITH orphaned AS (
    SELECT l.id
    FROM libraries AS l
    LEFT JOIN bookshelves AS b ON b.id = l.basement_bookshelf_id
    WHERE l.basement_bookshelf_id IS NOT NULL
      AND (b.id IS NULL OR b.library_id <> l.id OR b.is_basement IS DISTINCT FROM TRUE)
)
SELECT id FROM libraries
WHERE basement_bookshelf_id IS NULL
UNION
SELECT id FROM orphaned
ORDER BY id;
"""
)

FIND_BASEMENT_SQL = text(
    """\
SELECT id, is_basement
FROM bookshelves
WHERE library_id = :library_id
  AND (is_basement = TRUE OR LOWER(name) = 'basement')
ORDER BY is_basement DESC, created_at ASC
LIMIT 1;
"""
)

UPDATE_BOOKSHELF_SQL = text(
    """\
UPDATE bookshelves
SET is_basement = TRUE,
    name = 'Basement',
    status = 'active',
    updated_at = :updated_at
WHERE id = :bookshelf_id;
"""
)

INSERT_BASEMENT_SQL = text(
    """\
INSERT INTO bookshelves (
    id,
    library_id,
    name,
    description,
    is_basement,
    is_pinned,
    pinned_at,
    is_favorite,
    status,
    book_count,
    created_at,
    updated_at
) VALUES (
    :id,
    :library_id,
    'Basement',
    'Auto-generated Basement shelf',
    TRUE,
    FALSE,
    NULL,
    FALSE,
    'active',
    0,
    :now,
    :now
);
"""
)

UPDATE_LIBRARY_SQL = text(
    """\
UPDATE libraries
SET basement_bookshelf_id = :basement_id,
    updated_at = :updated_at
WHERE id = :library_id;
"""
)


async def ensure_column_and_constraint(conn) -> None:
    await conn.exec_driver_sql(ADD_COLUMN_SQL)
    result = await conn.execute(CHECK_CONSTRAINT_SQL)
    if not result.scalar():
        await conn.exec_driver_sql(ADD_CONSTRAINT_SQL)
    await conn.exec_driver_sql(UPSERT_BASEMENT_TRIGGER_SQL)


async def resolve_basement_for_library(conn, library_id):
    """Find or create the basement bookshelf for a single library."""
    result = await conn.execute(FIND_BASEMENT_SQL, {"library_id": library_id})
    row = result.first()
    now = datetime.now(timezone.utc)

    if row:
        basement_id, is_basement = row
        if not is_basement:
            await conn.execute(
                UPDATE_BOOKSHELF_SQL,
                {
                    "bookshelf_id": basement_id,
                    "updated_at": now,
                },
            )
        return basement_id, False

    # No existing basement bookshelf → create one
    basement_id = uuid4()
    await conn.execute(
        INSERT_BASEMENT_SQL,
        {
            "id": basement_id,
            "library_id": library_id,
            "now": now,
        },
    )
    return basement_id, True


async def backfill_libraries(conn) -> tuple[int, int, int]:
    result = await conn.execute(MISSING_OR_INVALID_LIBRARIES_SQL)
    library_ids = [row[0] for row in result]
    if not library_ids:
        return 0, 0, 0

    created = 0
    reused = 0
    for library_id in library_ids:
        basement_id, did_create = await resolve_basement_for_library(conn, library_id)
        await conn.execute(
            UPDATE_LIBRARY_SQL,
            {
                "library_id": library_id,
                "basement_id": basement_id,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        if did_create:
            created += 1
        else:
            reused += 1

    return len(library_ids), reused, created


async def run():
    engine = await get_engine()
    async with engine.begin() as conn:
        await ensure_column_and_constraint(conn)
        total, reused, created = await backfill_libraries(conn)
    await engine.dispose()
    print(
        f"[basement-backfill] processed={total} reused_existing={reused} created_new={created}"
    )


if __name__ == "__main__":
    loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run())
    finally:
        loop.close()