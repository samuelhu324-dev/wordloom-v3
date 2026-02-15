from __future__ import annotations

import argparse
from datetime import datetime, timezone

from sqlalchemy import create_engine, text


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Classify and replay terminal failed rows in search_outbox_events (wordloom_test)."
    )
    p.add_argument(
        "--database-url",
        default="postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test",
        help="SQLAlchemy URL (default points to devtest test DB)",
    )
    p.add_argument("--by", required=True, help="Operator identifier (audit)")
    p.add_argument("--reason", required=True, help="Replay reason (audit)")
    p.add_argument("--limit", type=int, default=100000, help="Max rows to replay")
    p.add_argument("--dry-run", action="store_true", help="Print counts but do not modify")
    return p.parse_args()


def _fetchall(conn, query: str):
    return conn.execute(text(query)).fetchall()


def main() -> int:
    args = _parse_args()

    engine = create_engine(args.database_url, pool_pre_ping=True)
    now = _utc_now()

    with engine.begin() as conn:
        db = conn.execute(text("select current_database()"))
        current_db = db.scalar()
        if current_db != "wordloom_test":
            raise SystemExit(f"Refusing to operate: expected current_database()=wordloom_test, got {current_db!r}")

        status_counts = _fetchall(
            conn,
            "select status, count(*) as n from search_outbox_events group by 1 order by n desc",
        )
        failed_buckets = _fetchall(
            conn,
            """
            select
              entity_type,
              op,
              attempts,
              coalesce(error_reason, '(null)') as error_reason,
              (coalesce(error,'') = '') as error_empty,
              count(*) as n,
              min(updated_at) as min_updated_at,
              max(updated_at) as max_updated_at
            from search_outbox_events
            where status = 'failed'
            group by 1,2,3,4,5
            order by n desc;
            """.strip(),
        )
        failed_total = conn.execute(text("select count(*) from search_outbox_events where status='failed'"))
        failed_total_n = int(failed_total.scalar() or 0)

        print("db=", current_db)
        print("status_counts=", status_counts)
        print("failed_total=", failed_total_n)
        print("failed_buckets=")
        for row in failed_buckets:
            print(tuple(row))

        to_replay = min(failed_total_n, max(0, int(args.limit)))
        print(f"will_replay={to_replay} (limit={args.limit})")

        if args.dry_run or to_replay <= 0:
            return 0

        result = conn.execute(
            text(
                """
                update search_outbox_events
                set
                  status = 'pending',
                  owner = null,
                  lease_until = null,
                  processing_started_at = null,
                  attempts = 0,
                  next_retry_at = null,
                  error_reason = null,
                  error = null,
                  replay_count = replay_count + 1,
                  last_replayed_at = :now,
                  last_replayed_by = :by,
                  last_replayed_reason = :reason,
                  updated_at = :now
                where status = 'failed'
                """
            ),
            {
                "now": now,
                "by": str(args.by)[:120],
                "reason": str(args.reason),
            },
        )
        changed = int(getattr(result, "rowcount", 0) or 0)
        print("replayed_rows=", changed)

        post_status_counts = _fetchall(
            conn,
            "select status, count(*) as n from search_outbox_events group by 1 order by n desc",
        )
        post_failed = conn.execute(text("select count(*) from search_outbox_events where status='failed'"))
        post_failed_n = int(post_failed.scalar() or 0)
        post_pending = conn.execute(text("select count(*) from search_outbox_events where status='pending'"))
        post_pending_n = int(post_pending.scalar() or 0)
        post_replayed = conn.execute(text("select count(*) from search_outbox_events where replay_count > 0"))
        post_replayed_n = int(post_replayed.scalar() or 0)

        print("post_status_counts=", post_status_counts)
        print("post_failed=", post_failed_n)
        print("post_pending=", post_pending_n)
        print("post_replay_count_gt0=", post_replayed_n)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
