"""Backfill Elasticsearch from Postgres `search_index`.

Chosen path: event_version + backfill.
- Reads rows from Postgres `search_index`.
- Writes docs into Elasticsearch via Bulk API.
- Stores event_version so Elastic stage1 can sort stably.

Env:
  DATABASE_URL     (default: postgresql://wordloom:wordloom@localhost:5435/wordloom_dev)
  ELASTIC_URL      (default: http://localhost:9200)
  ELASTIC_INDEX    (default: wordloom-search-index)

Run (PowerShell):
  $env:DATABASE_URL='postgresql://wordloom:wordloom@localhost:5435/wordloom_dev'
  $env:ELASTIC_URL='http://localhost:9200'
  python backend/scripts/backfill_elastic_search_index.py --recreate

Run (WSL):
  export DATABASE_URL='postgresql://wordloom:wordloom@localhost:5435/wordloom_dev'
  export ELASTIC_URL='http://localhost:9200'
  python3 backend/scripts/backfill_elastic_search_index.py --recreate
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import text


_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from infra.database.session import get_session_factory  # noqa: E402


def _elastic_url() -> str:
    return (os.getenv("ELASTIC_URL") or "http://localhost:9200").rstrip("/")


def _elastic_index() -> str:
    return os.getenv("ELASTIC_INDEX") or "wordloom-search-index"


def _http(method: str, url: str, *, body: bytes | None, content_type: str | None) -> tuple[int, str]:
    req = Request(url, data=body, method=method)
    req.add_header("Accept", "application/json")
    if content_type:
        req.add_header("Content-Type", content_type)

    try:
        with urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, payload
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        return e.code, detail
    except URLError as e:
        raise SystemExit(f"Elastic connection failed for {url}: {e}") from e


def _http_json(method: str, url: str, *, body: dict[str, Any] | None) -> dict[str, Any]:
    raw = None if body is None else json.dumps(body).encode("utf-8")
    status, payload = _http(method, url, body=raw, content_type="application/json" if raw else None)
    if status >= 400:
        raise SystemExit(f"Elastic HTTP {status} for {url}: {payload}")
    return json.loads(payload) if payload else {}


def ensure_index(*, recreate: bool) -> None:
    base = _elastic_url()
    index = _elastic_index()

    if recreate:
        _http("DELETE", f"{base}/{index}", body=None, content_type=None)

    # Create index if missing
    status, _ = _http("HEAD", f"{base}/{index}", body=None, content_type=None)
    if status == 200:
        return

    mapping = {
        "mappings": {
            "properties": {
                "entity_type": {"type": "keyword"},
                "entity_id": {"type": "keyword"},
                "text": {"type": "text"},
                "snippet": {"type": "text", "index": False},
                "rank_score": {"type": "float"},
                "event_version": {"type": "long"},
                "updated_at": {"type": "date"},
            }
        }
    }

    _http_json("PUT", f"{base}/{index}", body=mapping)


def _bulk_ndjson(lines: list[str]) -> dict[str, Any]:
    base = _elastic_url()
    index = _elastic_index()
    body = ("\n".join(lines) + "\n").encode("utf-8")

    status, payload = _http(
        "POST",
        f"{base}/{index}/_bulk",
        body=body,
        content_type="application/x-ndjson",
    )
    if status >= 400:
        raise SystemExit(f"Elastic bulk HTTP {status}: {payload}")
    return json.loads(payload) if payload else {}


async def backfill(*, batch_size: int) -> None:
    factory = await get_session_factory()

    # Use raw SQL for stable ordering + lower overhead.
    sql = text(
        """
        SELECT entity_type,
               entity_id::text AS entity_id,
               text,
               COALESCE(snippet, '') AS snippet,
               COALESCE(rank_score, 0) AS rank_score,
               COALESCE(event_version, 0) AS event_version,
               updated_at
        FROM search_index
        ORDER BY event_version ASC
        """
    )

    base = _elastic_url()
    index = _elastic_index()

    total = 0
    async with factory() as session:
        rows = (await session.execute(sql)).mappings().all()

    lines: list[str] = []
    for row in rows:
        doc_id = f"{row['entity_type']}:{row['entity_id']}"
        lines.append(json.dumps({"index": {"_index": index, "_id": doc_id}}))
        lines.append(
            json.dumps(
                {
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "text": row["text"] or "",
                    "snippet": row["snippet"] or "",
                    "rank_score": float(row["rank_score"]) if row.get("rank_score") is not None else 0.0,
                    "event_version": int(row["event_version"]) if row.get("event_version") is not None else 0,
                    "updated_at": (row["updated_at"].isoformat() if row.get("updated_at") else datetime.utcnow().isoformat()),
                }
            )
        )

        if len(lines) >= batch_size * 2:
            resp = _bulk_ndjson(lines)
            if resp.get("errors"):
                raise SystemExit(f"Elastic bulk had errors: {resp}")
            total += batch_size
            print(f"[backfill] indexed ~{total} docs")
            lines = []

    if lines:
        resp = _bulk_ndjson(lines)
        if resp.get("errors"):
            raise SystemExit(f"Elastic bulk had errors: {resp}")
        total += len(lines) // 2

    # Refresh for immediate search visibility.
    _http_json("POST", f"{base}/{index}/_refresh", body=None)

    print(f"[backfill] done. indexed={total}")


def main() -> None:
    if sys.platform == "win32":
        # psycopg async is incompatible with ProactorEventLoop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the index")
    parser.add_argument("--batch-size", type=int, default=500, help="Docs per bulk request")
    args = parser.parse_args()

    os.environ.setdefault(
        "DATABASE_URL", "postgresql://wordloom:wordloom@localhost:5435/wordloom_dev"
    )

    ensure_index(recreate=args.recreate)
    asyncio.run(backfill(batch_size=args.batch_size))


if __name__ == "__main__":
    main()
