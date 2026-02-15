"""Rebuild chronicle_entries from chronicle_events.

This is the Chronicle analogue to rebuild_search_index.py, but DB->DB.

Usage (WSL2/bash or PowerShell):
  export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
  python backend/scripts/rebuild_chronicle_entries.py --truncate

Options:
- --truncate: clears chronicle_entries before rebuild
- --emit-outbox: enqueue chronicle_outbox_events instead of writing entries directly
  (useful to validate the worker path)
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from infra.database.session import get_session_factory
from infra.database.models.chronicle_models import ChronicleEventModel
from infra.database.models.chronicle_entries_models import ChronicleEntryModel
from infra.database.models.chronicle_outbox_models import ChronicleOutboxEventModel
from infra.database.models.projection_status_models import ProjectionStatusModel


PROJECTION_NAME = "chronicle_events_to_entries"


class _NoopMetric:
    def labels(self, **_kwargs):  # noqa: ANN003
        return self

    def set(self, *_args, **_kwargs):  # noqa: ANN003
        return None


def _get_rebuild_metrics():
    """Best-effort metrics.

    Allow running rebuild tools in minimal environments where prometheus_client
    isn't installed (e.g., ad-hoc local interpreters). Metrics become no-ops.
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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _summarize(event: ChronicleEventModel) -> str:
    # Minimal deterministic summary. Intentionally conservative; evolve later.
    if event.block_id:
        return f"{event.event_type} (book={event.book_id}, block={event.block_id})"
    return f"{event.event_type} (book={event.book_id})"


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid int env {name}={raw!r}") from exc


def _get_projection_version() -> int:
    # Default to v1 to match current behavior.
    return _get_int_env("CHRONICLE_PROJECTION_VERSION", _get_int_env("OUTBOX_PROJECTION_VERSION", 1))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rebuild chronicle_entries from chronicle_events")
    p.add_argument("--truncate", action="store_true", help="Delete all rows in chronicle_entries first")
    p.add_argument("--emit-outbox", action="store_true", help="Enqueue chronicle_outbox_events instead of writing entries")
    p.add_argument("--limit", type=int, default=0, help="Optional limit (0 means no limit)")
    return p.parse_args()


async def _set_projection_status(session, *, success: bool, error: Optional[str], started_at: datetime, finished_at: datetime) -> None:
    duration = (finished_at - started_at).total_seconds()

    stmt = insert(ProjectionStatusModel).values(
        projection_name=PROJECTION_NAME,
        last_rebuild_started_at=started_at,
        last_rebuild_finished_at=finished_at,
        last_rebuild_duration_seconds=duration,
        last_rebuild_success=bool(success),
        last_rebuild_error=error,
        updated_at=finished_at,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[ProjectionStatusModel.projection_name],
        set_={
            "last_rebuild_started_at": started_at,
            "last_rebuild_finished_at": finished_at,
            "last_rebuild_duration_seconds": duration,
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

    session_factory = await get_session_factory()

    started_at = _utc_now()
    success = False
    error: Optional[str] = None

    try:
        async with session_factory() as session:
            if args.truncate and not args.emit_outbox:
                await session.execute(delete(ChronicleEntryModel))

            if args.truncate and args.emit_outbox:
                await session.execute(delete(ChronicleOutboxEventModel))

            limit = int(args.limit or 0)
            stmt = select(ChronicleEventModel).order_by(ChronicleEventModel.occurred_at.asc(), ChronicleEventModel.id.asc())
            if limit > 0:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            events = list(result.scalars().all())

            now = _utc_now()
            projection_version = _get_projection_version()

            if args.emit_outbox:
                # Enqueue pending outbox rows. Worker will materialize chronicle_entries.
                for ev in events:
                    session.add(
                        ChronicleOutboxEventModel(
                            entity_type="chronicle_event",
                            entity_id=ev.id,
                            op="upsert",
                            event_version=0,
                            status="pending",
                            attempts=0,
                            replay_count=0,
                            created_at=now,
                            updated_at=now,
                        )
                    )
            else:
                for ev in events:
                    stmt2 = insert(ChronicleEntryModel).values(
                        id=ev.id,
                        event_type=ev.event_type,
                        book_id=ev.book_id,
                        block_id=ev.block_id,
                        actor_id=ev.actor_id,
                        occurred_at=ev.occurred_at,
                        created_at=ev.created_at,
                        payload=ev.payload or {},
                        summary=_summarize(ev),
                        projection_version=projection_version,
                        updated_at=now,
                    )
                    stmt2 = stmt2.on_conflict_do_update(
                        index_elements=[ChronicleEntryModel.id],
                        set_={
                            "event_type": ev.event_type,
                            "book_id": ev.book_id,
                            "block_id": ev.block_id,
                            "actor_id": ev.actor_id,
                            "occurred_at": ev.occurred_at,
                            "created_at": ev.created_at,
                            "payload": ev.payload or {},
                            "summary": _summarize(ev),
                            "projection_version": projection_version,
                            "updated_at": now,
                        },
                    )
                    await session.execute(stmt2)

            finished_at = _utc_now()
            await _set_projection_status(session, success=True, error=None, started_at=started_at, finished_at=finished_at)
            await session.commit()
            success = True

            projection_rebuild_duration_seconds.labels(projection=PROJECTION_NAME).set((finished_at - started_at).total_seconds())
            projection_rebuild_last_finished_timestamp_seconds.labels(projection=PROJECTION_NAME).set(finished_at.timestamp())
            projection_rebuild_last_success.labels(projection=PROJECTION_NAME).set(1)

            print(
                f"Rebuild OK: events={len(events)} truncate={bool(args.truncate)} emit_outbox={bool(args.emit_outbox)}"
            )

        return 0
    except Exception as exc:
        error = str(exc)
        finished_at = _utc_now()
        try:
            async with session_factory() as session:
                await _set_projection_status(session, success=False, error=error, started_at=started_at, finished_at=finished_at)
                await session.commit()
        except Exception:
            pass

        projection_rebuild_last_finished_timestamp_seconds.labels(projection=PROJECTION_NAME).set(finished_at.timestamp())
        projection_rebuild_last_success.labels(projection=PROJECTION_NAME).set(0)

        raise


def main() -> None:
    import asyncio

    if sys.platform == "win32":
        # psycopg async is incompatible with ProactorEventLoop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":  # pragma: no cover
    main()
