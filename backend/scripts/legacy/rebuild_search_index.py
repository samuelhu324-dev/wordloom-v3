"""Rebuild Postgres `search_index` from Source-of-Truth tables.

This is the Search projection rebuild primitive:
- Reads SoT tables (books, blocks)
- Upserts into `search_index`
- Optionally emits `search_outbox_events` so the ES worker can replay updates

Usage (WSL2/bash or PowerShell):
  export DATABASE_URL='postgresql://wordloom:wordloom@localhost:5435/wordloom_test'
  python backend/scripts/rebuild_search_index.py --truncate --emit-outbox

Notes:
- This rebuild only covers entity types we currently project here: book + block.
- Soft-deleted rows are skipped.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# psycopg async cannot run on ProactorEventLoop. Force Selector policy on Windows.
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


from infra.database.session import get_session_factory
from infra.database.models.book_models import BookModel
from infra.database.models.block_models import BlockModel
from infra.database.models.search_index_models import SearchIndexModel
from infra.database.models.search_outbox_models import SearchOutboxEventModel
from infra.database.models.projection_status_models import ProjectionStatusModel


PROJECTION_NAME = "search_sot_to_search_index"


class _NoopMetric:
    def labels(self, **_kwargs):  # noqa: ANN003
        return self

    def set(self, *_args, **_kwargs):  # noqa: ANN003
        return None


def _get_rebuild_metrics():
    """Best-effort metrics.

    These are optional for ad-hoc scripts; allow running in minimal envs.
    """

    try:
        from infra.observability.outbox_metrics import (
            projection_rebuild_duration_seconds,
            projection_rebuild_last_finished_timestamp_seconds,
            projection_rebuild_last_success,
        )

        return (
            projection_rebuild_duration_seconds,
            projection_rebuild_last_finished_timestamp_seconds,
            projection_rebuild_last_success,
        )
    except Exception:
        noop = _NoopMetric()
        return (noop, noop, noop)


@dataclass(frozen=True)
class _Counters:
    books: int = 0
    blocks: int = 0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _event_version(ts: datetime) -> int:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # microseconds since epoch
    return int(ts.timestamp() * 1_000_000)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rebuild search_index from books + blocks")
    p.add_argument(
        "--truncate",
        action="store_true",
        help="Delete existing search_index rows for entity types book+block before rebuild",
    )
    p.add_argument(
        "--emit-outbox",
        action="store_true",
        help="Enqueue search_outbox_events for each upsert (worker will project to ES)",
    )
    p.add_argument("--batch-size", type=int, default=500, help="Commit every N rows (default: 500)")
    p.add_argument("--limit", type=int, default=0, help="Optional limit per entity type (0 means no limit)")
    return p.parse_args()


async def _set_projection_status(
    session,
    *,
    success: bool,
    error: Optional[str],
    started_at: datetime,
    finished_at: datetime,
) -> None:
    duration_s = max(0.0, (finished_at - started_at).total_seconds())
    stmt = pg_insert(ProjectionStatusModel).values(
        projection_name=PROJECTION_NAME,
        last_rebuild_started_at=started_at,
        last_rebuild_finished_at=finished_at,
        last_rebuild_duration_seconds=duration_s,
        last_rebuild_success=bool(success),
        last_rebuild_error=error,
        updated_at=finished_at,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[ProjectionStatusModel.projection_name],
        set_={
            "last_rebuild_started_at": started_at,
            "last_rebuild_finished_at": finished_at,
            "last_rebuild_duration_seconds": duration_s,
            "last_rebuild_success": bool(success),
            "last_rebuild_error": error,
            "updated_at": finished_at,
        },
    )
    await session.execute(stmt)


async def main_async() -> int:
    args = _parse_args()

    (
        projection_rebuild_duration_seconds,
        projection_rebuild_last_finished_timestamp_seconds,
        projection_rebuild_last_success,
    ) = _get_rebuild_metrics()

    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must be set")

    batch_size = int(args.batch_size or 0)
    if batch_size <= 0:
        raise RuntimeError("--batch-size must be > 0")

    limit = int(args.limit or 0)
    if limit < 0:
        raise RuntimeError("--limit must be >= 0")

    session_factory = await get_session_factory()

    started_at = _utc_now()
    success = False
    error: Optional[str] = None
    counters = _Counters()

    try:
        async with session_factory() as session:
            if args.truncate:
                await session.execute(
                    delete(SearchIndexModel).where(SearchIndexModel.entity_type.in_(["book", "block"]))
                )

            now = _utc_now()

            # --- Books ---
            books_stmt = (
                select(
                    BookModel.id,
                    BookModel.library_id,
                    BookModel.title,
                    BookModel.summary,
                    BookModel.updated_at,
                    BookModel.created_at,
                )
                .where(BookModel.soft_deleted_at.is_(None))
                .order_by(BookModel.created_at.asc(), BookModel.id.asc())
            )
            if limit > 0:
                books_stmt = books_stmt.limit(limit)
            book_rows = (await session.execute(books_stmt)).all()

            for (book_id, library_id, title, summary, updated_at, created_at) in book_rows:
                text = (title or "") + ("\n" + summary if summary else "")
                ts = updated_at or created_at or now
                version = _event_version(ts)

                stmt = pg_insert(SearchIndexModel).values(
                    entity_type="book",
                    library_id=library_id,
                    entity_id=book_id,
                    text=text,
                    snippet=(title or "")[:200],
                    rank_score=0.0,
                    created_at=created_at or ts,
                    updated_at=ts,
                    event_version=version,
                )
                excluded = stmt.excluded
                stmt = stmt.on_conflict_do_update(
                    index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id],
                    set_={
                        "library_id": excluded.library_id,
                        "text": excluded.text,
                        "snippet": excluded.snippet,
                        "updated_at": excluded.updated_at,
                        "event_version": excluded.event_version,
                    },
                    where=SearchIndexModel.event_version <= excluded.event_version,
                )
                await session.execute(stmt)

                if args.emit_outbox:
                    await session.execute(
                        pg_insert(SearchOutboxEventModel).values(
                            entity_type="book",
                            entity_id=book_id,
                            op="upsert",
                            event_version=version,
                            status="pending",
                            attempts=0,
                            replay_count=0,
                            created_at=now,
                            updated_at=now,
                        )
                    )

                counters = _Counters(books=counters.books + 1, blocks=counters.blocks)
                if counters.books % batch_size == 0:
                    await session.commit()

            await session.commit()

            # --- Blocks ---
            blocks_stmt = (
                select(
                    BlockModel.id,
                    BlockModel.book_id,
                    BlockModel.content,
                    BlockModel.updated_at,
                    BlockModel.created_at,
                    BookModel.library_id,
                )
                .select_from(BlockModel)
                .join(BookModel, BookModel.id == BlockModel.book_id)
                .where(BlockModel.soft_deleted_at.is_(None), BookModel.soft_deleted_at.is_(None))
                .order_by(BlockModel.created_at.asc(), BlockModel.id.asc())
            )
            if limit > 0:
                blocks_stmt = blocks_stmt.limit(limit)
            block_rows = (await session.execute(blocks_stmt)).all()

            for (block_id, _book_id, content, updated_at, created_at, library_id) in block_rows:
                ts = updated_at or created_at or now
                version = _event_version(ts)

                stmt = pg_insert(SearchIndexModel).values(
                    entity_type="block",
                    library_id=library_id,
                    entity_id=block_id,
                    text=content or "",
                    snippet=(content or "")[:200],
                    rank_score=0.0,
                    created_at=created_at or ts,
                    updated_at=ts,
                    event_version=version,
                )
                excluded = stmt.excluded
                stmt = stmt.on_conflict_do_update(
                    index_elements=[SearchIndexModel.entity_type, SearchIndexModel.entity_id],
                    set_={
                        "library_id": excluded.library_id,
                        "text": excluded.text,
                        "snippet": excluded.snippet,
                        "updated_at": excluded.updated_at,
                        "event_version": excluded.event_version,
                    },
                    where=SearchIndexModel.event_version <= excluded.event_version,
                )
                await session.execute(stmt)

                if args.emit_outbox:
                    await session.execute(
                        pg_insert(SearchOutboxEventModel).values(
                            entity_type="block",
                            entity_id=block_id,
                            op="upsert",
                            event_version=version,
                            status="pending",
                            attempts=0,
                            replay_count=0,
                            created_at=now,
                            updated_at=now,
                        )
                    )

                counters = _Counters(books=counters.books, blocks=counters.blocks + 1)
                if counters.blocks % batch_size == 0:
                    await session.commit()

            finished_at = _utc_now()
            await _set_projection_status(session, success=True, error=None, started_at=started_at, finished_at=finished_at)
            await session.commit()
            success = True

            projection_rebuild_duration_seconds.labels(projection=PROJECTION_NAME).set(
                (finished_at - started_at).total_seconds()
            )
            projection_rebuild_last_finished_timestamp_seconds.labels(projection=PROJECTION_NAME).set(
                finished_at.timestamp()
            )
            projection_rebuild_last_success.labels(projection=PROJECTION_NAME).set(1)

            print(
                "Rebuild OK: books=%s blocks=%s truncate=%s emit_outbox=%s"
                % (
                    counters.books,
                    counters.blocks,
                    bool(args.truncate),
                    bool(args.emit_outbox),
                )
            )
            return 0
    except Exception as exc:
        error = str(exc)
        finished_at = _utc_now()
        try:
            async with session_factory() as session:
                await _set_projection_status(
                    session,
                    success=False,
                    error=error,
                    started_at=started_at,
                    finished_at=finished_at,
                )
                await session.commit()
        except Exception:
            pass

        projection_rebuild_last_finished_timestamp_seconds.labels(projection=PROJECTION_NAME).set(
            finished_at.timestamp()
        )
        projection_rebuild_last_success.labels(projection=PROJECTION_NAME).set(0)

        raise


def main() -> None:
    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":  # pragma: no cover
    main()
