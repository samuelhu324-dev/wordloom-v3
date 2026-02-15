"""Utility script to inspect current Basement entries in the database."""
import asyncio
import pathlib
import sys
from typing import Any

from sqlalchemy import text

# Ensure backend package is importable when script executed directly
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from infra.database.session import get_engine


async def main() -> None:
    engine = await get_engine()
    async with engine.connect() as conn:
        count_result = await conn.execute(text("SELECT COUNT(*) FROM basement_entries"))
        total = count_result.scalar() or 0
        print(f"[basement] entries_total={total}")
        if total:
            rows = await conn.execute(
                text(
                    """
                    SELECT id, book_id, library_id, bookshelf_id, previous_bookshelf_id, moved_at
                    FROM basement_entries
                    ORDER BY moved_at DESC
                    LIMIT 10
                    """
                )
            )
            for row in rows.mappings():
                print(_format_row(row))
    await engine.dispose()


def _format_row(row: dict[str, Any]) -> str:
    return (
        f"id={row['id']} book_id={row['book_id']} lib={row['library_id']} "
        f"shelf={row['bookshelf_id']} prev={row['previous_bookshelf_id']} moved_at={row['moved_at']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
