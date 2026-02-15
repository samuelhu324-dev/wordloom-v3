"""Probe chronicle_entries for a given chronicle_event id.

Usage:
  # DATABASE_URL must be set
    OUTBOX_CHRONICLE_EVENT_ID=<uuid> python backend/scripts/labs/labs_009_probe_chronicle_entry.py

Output (stdout): single JSON object.
"""

from __future__ import annotations

import json
import os
import uuid

import psycopg


def _database_url_psycopg(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://")


def _table_columns(conn: psycopg.Connection, table_name: str) -> set[str]:
    sql = (
        "select column_name "
        "from information_schema.columns "
        "where table_schema = 'public' and table_name = %s"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (table_name,))
        return {row[0] for row in cur.fetchall()}


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    event_id_raw = (os.environ.get("OUTBOX_CHRONICLE_EVENT_ID") or "").strip()
    if not event_id_raw:
        raise SystemExit("OUTBOX_CHRONICLE_EVENT_ID is required")

    try:
        event_id = uuid.UUID(event_id_raw)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Invalid OUTBOX_CHRONICLE_EVENT_ID={event_id_raw!r}") from exc

    cs = _database_url_psycopg(database_url)
    with psycopg.connect(cs) as conn:
        cols = _table_columns(conn, "chronicle_entries")
        if not cols:
            raise SystemExit("chronicle_entries table not found")
        if "projection_version" not in cols:
            raise SystemExit("chronicle_entries.projection_version column not found")

        with conn.cursor() as cur:
            cur.execute(
                "select projection_version from chronicle_entries where id = %s",
                (event_id,),
            )
            row = cur.fetchone()

    result = {
        "chronicle_event_id": str(event_id),
        "found": bool(row is not None),
        "projection_version": int(row[0]) if row is not None and row[0] is not None else None,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
