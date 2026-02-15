"""Manual replay tool for chronicle outbox events.

Policy (v2):
- Automatic worker treats `failed` as terminal (won't claim again).
- Ops can explicitly replay failed rows back to pending, with audit fields.

Usage (PowerShell):
  $env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test"
  python backend/scripts/chronicle_outbox_replay_failed.py --by alice --reason "fixed projector" --limit 100 --dry-run
  python backend/scripts/chronicle_outbox_replay_failed.py --by alice --reason "fixed projector" --limit 100
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlalchemy import select, update, func

# Ensure backend root is on sys.path.
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from infra.database.session import get_session_factory
from infra.database.models.chronicle_outbox_models import ChronicleOutboxEventModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Replay terminal failed chronicle_outbox_events back to pending")
    p.add_argument("--by", required=True, help="Operator identifier (for audit)")
    p.add_argument("--reason", required=True, help="Why this replay is being done (for audit)")
    p.add_argument("--limit", type=int, default=1000, help="Max rows to replay")
    p.add_argument(
        "--ids",
        nargs="+",
        default=None,
        help="Optional list of outbox event IDs to replay (space-separated). If provided, only these rows are considered.",
    )
    p.add_argument("--entity-type", default=None, help="Filter by entity_type")
    p.add_argument("--since-hours", type=float, default=None, help="Only replay rows updated within last N hours")
    p.add_argument("--dry-run", action="store_true", help="Print count but do not modify")
    return p.parse_args()


async def main_async() -> int:
    args = _parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL must be set")

    now = _utc_now()
    session_factory = await get_session_factory()

    where = [ChronicleOutboxEventModel.status == "failed"]
    if args.ids:
        where.append(ChronicleOutboxEventModel.id.in_(list(args.ids)))
    if args.entity_type:
        where.append(ChronicleOutboxEventModel.entity_type == args.entity_type)
    if args.since_hours is not None:
        where.append(ChronicleOutboxEventModel.updated_at >= (now - timedelta(hours=float(args.since_hours))))

    async with session_factory() as session:
        total = (
            await session.execute(select(func.count()).select_from(ChronicleOutboxEventModel).where(*where))
        ).scalar_one()

        to_replay = min(int(total), max(0, int(args.limit)))
        print(f"Matched failed rows: {int(total)}; will replay: {to_replay} (limit={args.limit})")

        if args.dry_run or to_replay <= 0:
            return 0

        result = await session.execute(
            update(ChronicleOutboxEventModel)
            .where(*where)
            .values(
                status="pending",
                owner=None,
                lease_until=None,
                processing_started_at=None,
                attempts=0,
                next_retry_at=None,
                error_reason=None,
                error=None,
                replay_count=(ChronicleOutboxEventModel.replay_count + 1),
                last_replayed_at=now,
                last_replayed_by=str(args.by)[:120],
                last_replayed_reason=str(args.reason),
                updated_at=now,
            )
        )
        await session.commit()
        changed = int(getattr(result, "rowcount", 0) or 0)
        print(f"Replayed rows: {changed}")

    return 0


def main() -> None:
    import asyncio

    if sys.platform == "win32":
        # psycopg async is incompatible with ProactorEventLoop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":  # pragma: no cover
    main()
