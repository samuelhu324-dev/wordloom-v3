"""Backfill basement_entries from existing soft-deleted books."""
import asyncio
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text

# Ensure backend package importable
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from infra.database.session import get_engine

FETCH_MISSING_SQL = text(
    """
    SELECT
        b.id AS book_id,
        b.library_id,
        b.bookshelf_id,
        b.previous_bookshelf_id,
        b.title,
        b.summary,
        b.status,
        b.block_count,
        COALESCE(b.moved_to_basement_at, b.soft_deleted_at, b.updated_at, b.created_at) AS moved_at,
        COALESCE(b.created_at, timezone('utc', now())) AS created_at
    FROM books b
    WHERE b.soft_deleted_at IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM basement_entries e WHERE e.book_id = b.id
      )
    ORDER BY moved_at ASC;
    """
)

INSERT_ENTRY_SQL = text(
    """
    INSERT INTO basement_entries (
        id,
        book_id,
        library_id,
        bookshelf_id,
        previous_bookshelf_id,
        title_snapshot,
        summary_snapshot,
        status_snapshot,
        block_count_snapshot,
        moved_at,
        created_at
    ) VALUES (
        :id,
        :book_id,
        :library_id,
        :bookshelf_id,
        :previous_bookshelf_id,
        :title_snapshot,
        :summary_snapshot,
        :status_snapshot,
        :block_count_snapshot,
        :moved_at,
        :created_at
    )
    ON CONFLICT (book_id) DO NOTHING;
    """
)


async def main() -> None:
    engine = await get_engine()
    async with engine.begin() as conn:
        result = await conn.execute(FETCH_MISSING_SQL)
        rows = result.mappings().all()
        if not rows:
            print("[basement-backfill] no missing entries detected")
            return

        inserted = 0
        now = datetime.now(timezone.utc)
        for row in rows:
            moved_at = row["moved_at"] or now
            created_at = row["created_at"] or moved_at
            payload: dict[str, Any] = {
                "id": uuid4(),
                "book_id": row["book_id"],
                "library_id": row["library_id"],
                "bookshelf_id": row["bookshelf_id"],
                "previous_bookshelf_id": row["previous_bookshelf_id"],
                "title_snapshot": row["title"],
                "summary_snapshot": row["summary"],
                "status_snapshot": row["status"],
                "block_count_snapshot": row["block_count"],
                "moved_at": moved_at,
                "created_at": created_at,
            }
            await conn.execute(INSERT_ENTRY_SQL, payload)
            inserted += 1

    await engine.dispose()
    print(f"[basement-backfill] inserted {inserted} basement entries")


if __name__ == "__main__":
    asyncio.run(main())
