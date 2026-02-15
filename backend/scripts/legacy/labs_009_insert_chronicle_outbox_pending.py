"""Insert deterministic rows for Chronicle outbox experiments.

Creates a minimal chain:
  libraries -> bookshelves -> books -> chronicle_events -> chronicle_outbox_events (pending)

This helper exists to avoid shell quoting issues when triggering labs scenarios.

Usage:
  # DATABASE_URL must be set
    python backend/scripts/labs/labs_009_insert_chronicle_outbox_pending.py

Optional env vars:
  OUTBOX_CHRONICLE_EVENT_ID           (UUID)  If set, do NOT create library/books/book/event; only enqueue outbox row.
  OUTBOX_EVENT_TYPE                   (default: labs-009.projection_version)
  OUTBOX_OP                           (default: upsert)
  OUTBOX_EVENT_VERSION                (default: microsecond timestamp)
  OUTBOX_PAYLOAD_JSON                 (default: {})
  OUTBOX_TRACEPARENT / OUTBOX_TRACESTATE (optional)

Output (stdout): single JSON object with ids.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import uuid

import psycopg
from psycopg.types.json import Json


def _database_url_psycopg(database_url: str) -> str:
    # Allow reuse of SQLAlchemy-style URL.
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


def _table_column_types(conn: psycopg.Connection, table_name: str) -> dict[str, str]:
    sql = (
        "select column_name, udt_name "
        "from information_schema.columns "
        "where table_schema = 'public' and table_name = %s"
    )
    with conn.cursor() as cur:
        cur.execute(sql, (table_name,))
        return {row[0]: row[1] for row in cur.fetchall()}


def _insert_row(conn: psycopg.Connection, *, table: str, values: dict[str, object]) -> None:
    cols = _table_columns(conn, table)
    if not cols:
        raise RuntimeError(f"table not found: {table}")

    filtered = {k: v for k, v in values.items() if k in cols}
    if not filtered:
        raise RuntimeError(f"no matching columns to insert into {table}")

    columns = list(filtered.keys())
    placeholders = ",".join(["%s"] * len(columns))
    columns_sql = ", ".join(columns)
    sql = f"insert into {table} ({columns_sql}) values ({placeholders})"

    with conn.cursor() as cur:
        cur.execute(sql, tuple(filtered[c] for c in columns))


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    reuse_event_id_raw = (os.environ.get("OUTBOX_CHRONICLE_EVENT_ID") or "").strip() or None

    event_type = os.environ.get("OUTBOX_EVENT_TYPE", "labs-009.projection_version")
    op = os.environ.get("OUTBOX_OP", "upsert")
    payload_json = os.environ.get("OUTBOX_PAYLOAD_JSON", "{}")
    traceparent = os.environ.get("OUTBOX_TRACEPARENT")
    tracestate = os.environ.get("OUTBOX_TRACESTATE")

    now = dt.datetime.now(dt.timezone.utc)

    raw_event_version = (os.environ.get("OUTBOX_EVENT_VERSION") or "").strip()
    if raw_event_version:
        event_version = int(raw_event_version)
    else:
        event_version = int(now.timestamp() * 1_000_000)

    cs = _database_url_psycopg(database_url)
    with psycopg.connect(cs) as conn:
        outbox_types = _table_column_types(conn, "chronicle_outbox_events")
        events_types = _table_column_types(conn, "chronicle_events")

        library_id = uuid.uuid4()
        bookshelf_id = uuid.uuid4()
        book_id = uuid.uuid4()

        if reuse_event_id_raw:
            chronicle_event_id = uuid.UUID(reuse_event_id_raw)
        else:
            chronicle_event_id = uuid.uuid4()

        # Create the minimal FK chain only if we're not reusing an existing event.
        if not reuse_event_id_raw:
            # libraries
            lib_values: dict[str, object] = {
                "id": library_id,
                "user_id": uuid.uuid4(),
                "name": "labs-009 library",
                "description": "labs-009 projection_version",
                "created_at": now,
                "updated_at": now,
                "last_activity_at": now,
                "views_count": 0,
                "pinned": False,
            }
            _insert_row(conn, table="libraries", values=lib_values)

            # bookshelves
            shelf_values: dict[str, object] = {
                "id": bookshelf_id,
                "library_id": library_id,
                "name": "labs-009 shelf",
                "description": "labs-009 projection_version",
                "is_basement": False,
                "is_pinned": False,
                "is_favorite": False,
                "status": "active",
                "book_count": 0,
                "created_at": now,
                "updated_at": now,
            }
            _insert_row(conn, table="bookshelves", values=shelf_values)

            # books
            book_values: dict[str, object] = {
                "id": book_id,
                "bookshelf_id": bookshelf_id,
                "library_id": library_id,
                "title": "labs-009 book",
                "summary": "labs-009 projection_version",
                "status": "draft",
                "maturity": "seed",
                "is_pinned": False,
                "block_count": 0,
                "maturity_score": 0,
                "legacy_flag": False,
                "manual_maturity_override": False,
                "visit_count_90d": 0,
                "created_at": now,
                "updated_at": now,
            }
            _insert_row(conn, table="books", values=book_values)

            # chronicle_events
            payload_obj: object
            try:
                payload_obj = json.loads(payload_json)
            except Exception:
                payload_obj = payload_json

            if isinstance(payload_obj, (dict, list)):
                payload_obj = Json(payload_obj)

            # Handle UUID columns that might be text in older schemas.
            def _uuid_or_text(col: str, value: uuid.UUID) -> object:
                if events_types.get(col) == "uuid":
                    return value
                return str(value)

            chron_values: dict[str, object] = {
                "id": _uuid_or_text("id", chronicle_event_id),
                "event_type": event_type,
                "book_id": _uuid_or_text("book_id", book_id),
                "block_id": None,
                "actor_id": None,
                "payload": payload_obj,
                "occurred_at": now,
                "created_at": now,
                # optional columns (will be filtered if missing)
                "schema_version": 1,
                "provenance": "labs-009",
                "source": "labs-009",
                "actor_kind": "unknown",
                "correlation_id": f"labs-009-{chronicle_event_id}",
            }
            _insert_row(conn, table="chronicle_events", values=chron_values)
        else:
            # If reusing event, we don't know book/library ids.
            library_id = None  # type: ignore[assignment]
            bookshelf_id = None  # type: ignore[assignment]
            book_id = None  # type: ignore[assignment]

        outbox_event_id = uuid.uuid4()

        # Outbox entity_id is UUID in current schema; support legacy text too.
        entity_id_val: object
        if outbox_types.get("entity_id") == "uuid":
            entity_id_val = chronicle_event_id
        else:
            entity_id_val = str(chronicle_event_id)

        outbox_values: dict[str, object] = {
            "id": outbox_event_id,
            "entity_type": "chronicle_event",
            "entity_id": entity_id_val,
            "op": op,
            "event_version": event_version,
            "created_at": now,
            "status": "pending",
            "attempts": 0,
            "replay_count": 0,
            "updated_at": now,
            "traceparent": traceparent,
            "tracestate": tracestate,
        }
        _insert_row(conn, table="chronicle_outbox_events", values=outbox_values)
        conn.commit()

    result = {
        "chronicle_event_id": str(chronicle_event_id),
        "outbox_event_id": str(outbox_event_id),
        "library_id": str(library_id) if library_id is not None else None,
        "bookshelf_id": str(bookshelf_id) if bookshelf_id is not None else None,
        "book_id": str(book_id) if book_id is not None else None,
        "event_type": str(event_type),
        "op": str(op),
        "event_version": int(event_version),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
