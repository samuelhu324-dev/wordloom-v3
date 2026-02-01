"""Search Outbox → Elasticsearch worker.

Continuously pulls unprocessed rows from search_outbox_events and
applies them to the Elasticsearch index.

Intended usage (from repo root, Windows PowerShell):

    $env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_dev"
    $env:ELASTIC_URL = "http://localhost:9200"
    $env:ELASTIC_INDEX = "wordloom-search-index"
    python backend/scripts/search_outbox_worker.py

The worker is deliberately simple: single-threaded, best-effort retries
(by leaving error rows with processed_at = NULL so they can be retried).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import socket
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Any
from pathlib import Path
from dataclasses import dataclass

import httpx
from prometheus_client import start_http_server
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend root is on sys.path so `infra.*` imports work whether this
# script is run from the repo root (python backend/scripts/...) or from
# backend/ directly (python scripts/...).
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from infra.database.session import get_session_factory
from infra.database.models.search_index_models import SearchIndexModel
from infra.database.models.search_outbox_models import SearchOutboxEventModel
from infra.observability.outbox_metrics import (
    outbox_failed_total,
    outbox_lag_events,
    outbox_processed_total,
    outbox_es_bulk_item_failures_total,
    outbox_es_bulk_items_total,
    outbox_es_bulk_request_duration_seconds,
    outbox_es_bulk_requests_total,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PROJECTION_NAME = "search_index_to_elastic"


@dataclass(frozen=True)
class _OutboxEventRow:
    id: Any
    entity_type: str
    entity_id: Any
    op: str
    event_version: int
    attempts: int


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid int env {name}={raw!r}") from exc


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid float env {name}={raw!r}") from exc


def _es_doc_id(entity_type: str, entity_id: Any) -> str:
    return f"{entity_type}:{entity_id}"


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _classify_status_code(status_code: int | None) -> str:
    if status_code is None:
        return "unknown"
    if status_code == 429:
        return "429"
    if 400 <= status_code < 500:
        return "4xx"
    if 500 <= status_code < 600:
        return "5xx"
    return "other"


def _try_parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_es_bulk_payload(
    *,
    index: str,
    ops: list[tuple[str, str, dict[str, Any] | None]],
) -> str:
    """Build NDJSON payload for Elasticsearch _bulk.

    ops: list of (op, doc_id, doc_or_none)
      op: "index" | "delete"
    """

    lines: list[str] = []
    for op, doc_id, doc in ops:
        if op == "index":
            lines.append(json.dumps({"index": {"_index": index, "_id": doc_id}}))
            lines.append(json.dumps(doc or {}))
        elif op == "delete":
            lines.append(json.dumps({"delete": {"_index": index, "_id": doc_id}}))
        else:
            raise ValueError(f"Unknown bulk op: {op!r}")
    return "\n".join(lines) + ("\n" if lines else "")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _compute_backoff_seconds(*, attempt: int, base: float, max_backoff: float) -> float:
    # Exponential backoff with jitter.
    exp = min(max_backoff, base * (2 ** max(0, attempt)))
    jitter = random.uniform(0.0, min(1.0, exp * 0.1))
    return min(max_backoff, exp + jitter)


async def _process_upsert(session: AsyncSession, client: httpx.AsyncClient, index: str, event: _OutboxEventRow) -> None:
    row = (
        await session.execute(
            select(SearchIndexModel).where(
                SearchIndexModel.entity_type == event.entity_type,
                SearchIndexModel.entity_id == event.entity_id,
            )
        )
    ).scalar_one_or_none()

    if row is None:
        # Nothing to upsert anymore (deleted or never existed); treat as success.
        logger.info("Outbox upsert: no search_index row for %s %s, skipping", event.entity_type, event.entity_id)
        return

    doc = {
        "entity_type": row.entity_type,
        "entity_id": str(row.entity_id),
        "text": row.text,
        "snippet": row.snippet,
        "rank_score": row.rank_score,
        "event_version": int(row.event_version),
    }

    doc_id = _es_doc_id(row.entity_type, row.entity_id)
    resp = await client.put(f"/{index}/_doc/{doc_id}", json=doc)
    resp.raise_for_status()
    logger.info(
        "Outbox upsert: indexed %s %s (version=%s) into ES", row.entity_type, row.entity_id, row.event_version
    )


async def _process_delete(client: httpx.AsyncClient, index: str, event: _OutboxEventRow) -> None:
    doc_id = _es_doc_id(event.entity_type, event.entity_id)
    resp = await client.delete(f"/{index}/_doc/{doc_id}")
    # 404 is fine (already deleted).
    if resp.status_code not in (200, 404):
        resp.raise_for_status()
    logger.info("Outbox delete: deleted %s from ES", doc_id)


async def _worker_loop() -> None:
    db_url = os.getenv("DATABASE_URL")
    es_url = os.getenv("ELASTIC_URL", "http://localhost:9200").rstrip("/")
    es_index = os.getenv("ELASTIC_INDEX", "wordloom-search-index")
    metrics_port = int(os.getenv("OUTBOX_METRICS_PORT", "9108"))

    # Tuning knobs (Phase 1: make throughput/lag observable & adjustable)
    batch_size = _get_int_env("OUTBOX_BULK_SIZE", 100)
    concurrency = _get_int_env("OUTBOX_CONCURRENCY", 1)
    poll_interval_seconds = _get_float_env("OUTBOX_POLL_INTERVAL_SECONDS", 1.0)
    use_es_bulk_api = _get_bool_env("OUTBOX_USE_ES_BULK", False)

    worker_id = os.getenv("OUTBOX_WORKER_ID")
    if not worker_id:
        worker_id = f"{socket.gethostname()}:{os.getpid()}"

    lease_seconds = _get_int_env("OUTBOX_LEASE_SECONDS", 30)
    max_attempts = _get_int_env("OUTBOX_MAX_ATTEMPTS", 10)
    base_backoff_seconds = _get_float_env("OUTBOX_BASE_BACKOFF_SECONDS", 0.5)
    max_backoff_seconds = _get_float_env("OUTBOX_MAX_BACKOFF_SECONDS", 30.0)
    reclaim_interval_seconds = _get_float_env("OUTBOX_RECLAIM_INTERVAL_SECONDS", 5.0)
    poll_interval_ms = os.getenv("OUTBOX_POLL_INTERVAL_MS")
    if poll_interval_ms:
        poll_interval_seconds = _get_int_env("OUTBOX_POLL_INTERVAL_MS", 1000) / 1000.0

    if batch_size <= 0:
        raise RuntimeError("OUTBOX_BULK_SIZE must be > 0")
    if concurrency <= 0:
        raise RuntimeError("OUTBOX_CONCURRENCY must be > 0")
    if poll_interval_seconds < 0:
        raise RuntimeError("OUTBOX_POLL_INTERVAL_SECONDS must be >= 0")

    if not db_url:
        raise RuntimeError("DATABASE_URL must be set")

    logger.info(
        "Search outbox worker starting: db=%s, es=%s index=%s, bulk=%s, concurrency=%s, poll=%.3fs, worker_id=%s, lease=%ss",
        db_url,
        es_url,
        es_index,
        batch_size,
        concurrency,
        poll_interval_seconds,
        worker_id,
        lease_seconds,
    )

    if use_es_bulk_api and concurrency != 1:
        logger.info("OUTBOX_USE_ES_BULK enabled: OUTBOX_CONCURRENCY is ignored (bulk uses one request per poll)")

    # Expose Prometheus metrics for this worker process.
    start_http_server(metrics_port)
    logger.info("Outbox worker metrics listening on :%s", metrics_port)

    # Pre-warm metric series so they show up even when zero.
    outbox_processed_total.labels(projection=PROJECTION_NAME, op="upsert").inc(0)
    outbox_processed_total.labels(projection=PROJECTION_NAME, op="delete").inc(0)
    outbox_failed_total.labels(projection=PROJECTION_NAME, op="upsert", reason="none").inc(0)
    outbox_failed_total.labels(projection=PROJECTION_NAME, op="delete", reason="none").inc(0)
    outbox_lag_events.labels(projection=PROJECTION_NAME).set(0)

    # Bulk request metrics warm-up
    outbox_es_bulk_requests_total.labels(projection=PROJECTION_NAME, result="success").inc(0)
    outbox_es_bulk_requests_total.labels(projection=PROJECTION_NAME, result="partial").inc(0)
    outbox_es_bulk_requests_total.labels(projection=PROJECTION_NAME, result="failed").inc(0)
    outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op="index", result="success").inc(0)
    outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op="index", result="failed").inc(0)
    outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op="delete", result="success").inc(0)
    outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op="delete", result="failed").inc(0)
    for cls in ("429", "4xx", "5xx", "unknown", "other"):
        outbox_es_bulk_item_failures_total.labels(projection=PROJECTION_NAME, op="index", failure_class=cls).inc(0)
        outbox_es_bulk_item_failures_total.labels(projection=PROJECTION_NAME, op="delete", failure_class=cls).inc(0)

    session_factory = await get_session_factory()

    # Safety fuse: ensure this worker is pointed at the intended DB.
    expected_env = os.getenv("WORDLOOM_ENV")
    if expected_env:
        from infra.database.env_guard import assert_expected_database_environment

        async with session_factory() as session:
            await assert_expected_database_environment(session)
        logger.info("[ENV_GUARD] Database environment check: OK")

    semaphore = asyncio.Semaphore(concurrency)
    entity_locks: dict[str, asyncio.Lock] = {}

    async def _sanitize_terminal_rows() -> None:
        """Best-effort repair: terminal rows must not retain ownership/leases.

        Invariants:
        - status in {done, failed} => owner is NULL and lease_until is NULL
        - processed_at IS NOT NULL => owner is NULL and lease_until is NULL

        This protects correctness if anything (including manual experiments) leaves
        stray owner/lease values behind.
        """

        now = _utc_now()
        async with session_factory() as session:
            result = await session.execute(
                update(SearchOutboxEventModel)
                .where(
                    (
                        SearchOutboxEventModel.processed_at.is_not(None)
                        | SearchOutboxEventModel.status.in_(["done", "failed"])
                    ),
                    (SearchOutboxEventModel.owner.is_not(None) | SearchOutboxEventModel.lease_until.is_not(None)),
                )
                .values(
                    owner=None,
                    lease_until=None,
                    updated_at=now,
                )
            )
            await session.commit()
            fixed = int(getattr(result, "rowcount", 0) or 0)
            if fixed:
                logger.warning("Sanitized %s terminal outbox rows with stray owner/lease", fixed)

    async def _reclaim_expired_leases() -> None:
        if reclaim_interval_seconds <= 0:
            return
        now = _utc_now()
        async with session_factory() as session:
            session = session
            result = await session.execute(
                update(SearchOutboxEventModel)
                .where(
                    SearchOutboxEventModel.processed_at.is_(None),
                    SearchOutboxEventModel.status == "processing",
                    SearchOutboxEventModel.lease_until.is_not(None),
                    SearchOutboxEventModel.lease_until < now,
                )
                .values(
                    status="pending",
                    owner=None,
                    lease_until=None,
                    updated_at=now,
                )
            )
            await session.commit()
            reclaimed = int(getattr(result, "rowcount", 0) or 0)
            if reclaimed:
                logger.warning("Reclaimed %s expired outbox leases", reclaimed)

    async def _renew_lease(session: AsyncSession, ids: list[Any]) -> None:
        if not ids:
            return
        now = _utc_now()
        await session.execute(
            update(SearchOutboxEventModel)
            .where(
                SearchOutboxEventModel.id.in_(ids),
                SearchOutboxEventModel.processed_at.is_(None),
                SearchOutboxEventModel.status == "processing",
                SearchOutboxEventModel.owner == worker_id,
            )
            .values(
                lease_until=now + timedelta(seconds=lease_seconds),
                updated_at=now,
            )
        )

    def _lease_until(now: datetime) -> datetime:
        return now + timedelta(seconds=lease_seconds)


    def _entity_key(entity_type: str, entity_id: Any) -> str:
        return f"{entity_type}:{entity_id}"

    def _get_entity_lock(entity_type: str, entity_id: Any) -> asyncio.Lock:
        key = _entity_key(entity_type, entity_id)
        lock = entity_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            entity_locks[key] = lock
        return lock

    def _should_retry_failure_class(failure_class: str) -> bool:
        # Policy: retry on 429 and server-side failures/timeouts.
        return failure_class in {"429", "5xx", "unknown"}

    def _is_permanent_failure_class(failure_class: str) -> bool:
        # Policy: treat most 4xx as non-retryable (e.g., mapping/parsing).
        return failure_class in {"4xx", "other"}

    def _classify_exception(exc: Exception) -> tuple[str, int | None]:
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            return _classify_status_code(status_code), status_code
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
            return "5xx", None
        return "unknown", None

    async def _process_one(ev: _OutboxEventRow, client: httpx.AsyncClient) -> None:
        # Concurrency guard: global cap + per-entity ordering.
        async with semaphore:
            async with _get_entity_lock(ev.entity_type, ev.entity_id):
                async with session_factory() as session:
                    session = session  # help type checkers (AsyncSession)
                    try:
                        # Reload row to confirm ownership/lease before doing work.
                        db_ev = (
                            await session.execute(
                                select(SearchOutboxEventModel).where(SearchOutboxEventModel.id == ev.id)
                            )
                        ).scalar_one_or_none()

                        if db_ev is None:
                            return

                        now = _utc_now()
                        if db_ev.processed_at is not None:
                            return
                        if db_ev.status != "processing" or db_ev.owner != worker_id:
                            return
                        if db_ev.lease_until is None or db_ev.lease_until <= now:
                            # Lease expired; let reclaim handle it.
                            return

                        if db_ev.op == "upsert":
                            await _process_upsert(session, client, es_index, ev)
                        elif db_ev.op == "delete":
                            await _process_delete(client, es_index, ev)
                        else:
                            raise ValueError(f"Unknown outbox op: {db_ev.op!r}")

                        await session.execute(
                            update(SearchOutboxEventModel)
                            .where(
                                SearchOutboxEventModel.id == db_ev.id,
                                SearchOutboxEventModel.owner == worker_id,
                                SearchOutboxEventModel.status == "processing",
                                SearchOutboxEventModel.lease_until > now,
                            )
                            .values(
                                status="done",
                                processed_at=now,
                                owner=None,
                                lease_until=None,
                                next_retry_at=None,
                                error=None,
                                updated_at=now,
                            )
                        )
                        await session.commit()

                        outbox_processed_total.labels(projection=PROJECTION_NAME, op=db_ev.op).inc()
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Failed to process outbox event %s", ev.id)

                        failure_class, _status_code = _classify_exception(exc)
                        attempts = int(getattr(ev, "attempts", 0) or 0)
                        next_attempt = attempts + 1

                        now = _utc_now()
                        if _should_retry_failure_class(failure_class) and next_attempt < max_attempts:
                            delay = _compute_backoff_seconds(
                                attempt=next_attempt,
                                base=base_backoff_seconds,
                                max_backoff=max_backoff_seconds,
                            )
                            next_retry_at = now + timedelta(seconds=delay)
                            values = {
                                "status": "pending",
                                "owner": None,
                                "lease_until": None,
                                "attempts": next_attempt,
                                "next_retry_at": next_retry_at,
                                "error": str(exc),
                                "updated_at": now,
                            }
                        else:
                            values = {
                                "status": "failed" if _is_permanent_failure_class(failure_class) else "failed",
                                "owner": None,
                                "lease_until": None,
                                "attempts": next_attempt,
                                "next_retry_at": None,
                                "error": str(exc),
                                "updated_at": now,
                            }

                        await session.execute(
                            update(SearchOutboxEventModel)
                            .where(
                                SearchOutboxEventModel.id == ev.id,
                                SearchOutboxEventModel.owner == worker_id,
                                SearchOutboxEventModel.status == "processing",
                                SearchOutboxEventModel.lease_until > now,
                            )
                            .values(**values)
                        )
                        await session.commit()

                        outbox_failed_total.labels(
                            projection=PROJECTION_NAME,
                            op=str(getattr(ev, "op", "unknown")),
                            reason=f"{type(exc).__name__}:{failure_class}",
                        ).inc()

    async with httpx.AsyncClient(base_url=es_url, timeout=10.0) as client:
        last_reclaim_at = 0.0
        while True:
            now_monotonic = time.monotonic()
            if reclaim_interval_seconds > 0 and (now_monotonic - last_reclaim_at) >= reclaim_interval_seconds:
                await _sanitize_terminal_rows()
                await _reclaim_expired_leases()
                last_reclaim_at = now_monotonic

            # Claim a batch of pending events with SKIP LOCKED.
            async with session_factory() as session:
                session = session

                now = _utc_now()
                pending_count = (
                    await session.execute(
                        select(func.count()).select_from(SearchOutboxEventModel).where(
                            SearchOutboxEventModel.processed_at.is_(None),
                            SearchOutboxEventModel.status.in_(["pending", "processing"]),
                        )
                    )
                ).scalar_one()
                outbox_lag_events.labels(projection=PROJECTION_NAME).set(int(pending_count))

                claimable = (
                    await session.execute(
                        select(SearchOutboxEventModel)
                        .where(
                            SearchOutboxEventModel.processed_at.is_(None),
                            SearchOutboxEventModel.status == "pending",
                            (SearchOutboxEventModel.next_retry_at.is_(None) | (SearchOutboxEventModel.next_retry_at <= now)),
                        )
                        .order_by(SearchOutboxEventModel.event_version.asc())
                        .with_for_update(skip_locked=True)
                        .limit(batch_size)
                    )
                ).scalars().all()

                if claimable:
                    ids = [row.id for row in claimable]
                    await session.execute(
                        update(SearchOutboxEventModel)
                        .where(SearchOutboxEventModel.id.in_(ids))
                        .values(
                            status="processing",
                            owner=worker_id,
                            lease_until=_lease_until(now),
                            updated_at=now,
                            error=None,
                        )
                    )
                    await session.commit()
                else:
                    ids = []

            if not claimable:
                await asyncio.sleep(poll_interval_seconds)
                continue

            events = [
                _OutboxEventRow(
                    id=row.id,
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    op=row.op,
                    event_version=int(row.event_version or 0),
                    attempts=int(row.attempts or 0),
                )
                for row in claimable
            ]

            # Process a batch with bounded concurrency. Per-entity lock prevents
            # out-of-order writes for the same entity when concurrency > 1.
            if not use_es_bulk_api:
                await asyncio.gather(*[_process_one(ev, client) for ev in events])
                continue

            # Bulk mode: turn the polled rows into one ES _bulk request.
            attempts_by_id = {ev.id: int(ev.attempts or 0) for ev in events}

            # Build bulk payload and apply immediate acks (no ES request needed).
            async with session_factory() as session:
                session = session

                bulk_ops: list[tuple[str, str, dict[str, Any] | None]] = []
                bulk_event_ids: list[Any] = []
                bulk_item_ops: list[str] = []
                bulk_outbox_ops: list[str] = []
                processed_immediately_ids: list[Any] = []
                failed_immediately: list[tuple[Any, str, str]] = []  # (id, op, reason)

                for ev in events:
                    if ev.op == "upsert":
                        row = (
                            await session.execute(
                                select(SearchIndexModel).where(
                                    SearchIndexModel.entity_type == ev.entity_type,
                                    SearchIndexModel.entity_id == ev.entity_id,
                                )
                            )
                        ).scalar_one_or_none()

                        if row is None:
                            processed_immediately_ids.append(ev.id)
                            continue

                        doc = {
                            "entity_type": row.entity_type,
                            "entity_id": str(row.entity_id),
                            "text": row.text,
                            "snippet": row.snippet,
                            "rank_score": row.rank_score,
                            "event_version": int(row.event_version),
                        }
                        doc_id = _es_doc_id(row.entity_type, row.entity_id)
                        bulk_ops.append(("index", doc_id, doc))
                        bulk_event_ids.append(ev.id)
                        bulk_item_ops.append("index")
                        bulk_outbox_ops.append("upsert")
                    elif ev.op == "delete":
                        doc_id = _es_doc_id(ev.entity_type, ev.entity_id)
                        bulk_ops.append(("delete", doc_id, None))
                        bulk_event_ids.append(ev.id)
                        bulk_item_ops.append("delete")
                        bulk_outbox_ops.append("delete")
                    else:
                        failed_immediately.append((ev.id, "unknown", "unknown_op"))

                now = _utc_now()

                if processed_immediately_ids:
                    await session.execute(
                        update(SearchOutboxEventModel)
                        .where(
                            SearchOutboxEventModel.id.in_(processed_immediately_ids),
                            SearchOutboxEventModel.owner == worker_id,
                            SearchOutboxEventModel.status == "processing",
                            SearchOutboxEventModel.lease_until > now,
                        )
                        .values(
                            status="done",
                            processed_at=now,
                            owner=None,
                            lease_until=None,
                            next_retry_at=None,
                            error=None,
                            updated_at=now,
                        )
                    )
                    for _id in processed_immediately_ids:
                        outbox_processed_total.labels(projection=PROJECTION_NAME, op="upsert").inc()

                for ev_id, op, reason in failed_immediately:
                    await session.execute(
                        update(SearchOutboxEventModel)
                        .where(
                            SearchOutboxEventModel.id == ev_id,
                            SearchOutboxEventModel.owner == worker_id,
                            SearchOutboxEventModel.status == "processing",
                            SearchOutboxEventModel.lease_until > now,
                        )
                        .values(
                            status="failed",
                            owner=None,
                            lease_until=None,
                            attempts=(attempts_by_id.get(ev_id, 0) + 1),
                            next_retry_at=None,
                            error=reason,
                            updated_at=now,
                        )
                    )
                    outbox_failed_total.labels(projection=PROJECTION_NAME, op=op, reason=reason).inc()

                await session.commit()

                if not bulk_ops:
                    continue

                payload = _build_es_bulk_payload(index=es_index, ops=bulk_ops)

            # Renew lease before the ES request.
            async with session_factory() as session:
                session = session
                await _renew_lease(session, [ev.id for ev in events])
                await session.commit()

            started = time.perf_counter()
            resp: httpx.Response | None = None
            request_result = "failed"
            try:
                resp = await client.post(
                    "/_bulk",
                    content=payload.encode("utf-8"),
                    headers={"Content-Type": "application/x-ndjson"},
                )
                request_result = "failed" if resp.status_code >= 400 else "success"
            except Exception as exc:  # noqa: BLE001
                logger.exception("ES bulk request failed")
                outbox_es_bulk_request_duration_seconds.labels(projection=PROJECTION_NAME).observe(
                    time.perf_counter() - started
                )

                # Treat as retryable failure for all items.
                now = _utc_now()
                async with session_factory() as session:
                    session = session
                    for idx, ev_id in enumerate(bulk_event_ids):
                        op = bulk_item_ops[idx]
                        outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op=op, result="failed").inc()
                        outbox_es_bulk_item_failures_total.labels(
                            projection=PROJECTION_NAME,
                            op=op,
                            failure_class="5xx",
                        ).inc()

                        attempts = attempts_by_id.get(ev_id, 0)
                        next_attempt = attempts + 1
                        delay = _compute_backoff_seconds(
                            attempt=next_attempt,
                            base=base_backoff_seconds,
                            max_backoff=max_backoff_seconds,
                        )
                        next_retry_at = now + timedelta(seconds=delay)

                        await session.execute(
                            update(SearchOutboxEventModel)
                            .where(
                                SearchOutboxEventModel.id == ev_id,
                                SearchOutboxEventModel.owner == worker_id,
                                SearchOutboxEventModel.status == "processing",
                                SearchOutboxEventModel.lease_until > now,
                            )
                            .values(
                                status="pending" if next_attempt < max_attempts else "failed",
                                owner=None,
                                lease_until=None,
                                attempts=next_attempt,
                                next_retry_at=(next_retry_at if next_attempt < max_attempts else None),
                                error=str(exc),
                                updated_at=now,
                            )
                        )

                        outbox_failed_total.labels(
                            projection=PROJECTION_NAME,
                            op=bulk_outbox_ops[idx],
                            reason=f"es_exception:{type(exc).__name__}",
                        ).inc()

                    await session.commit()

                outbox_es_bulk_requests_total.labels(projection=PROJECTION_NAME, result="failed").inc()
                continue

            outbox_es_bulk_request_duration_seconds.labels(projection=PROJECTION_NAME).observe(
                time.perf_counter() - started
            )

            success_ids: list[Any] = []
            failure_ids: list[Any] = []
            failure_classes: list[str | None] = [None] * len(bulk_event_ids)

            body: Any
            try:
                body = resp.json() if resp is not None else None
            except Exception:  # noqa: BLE001
                body = None

            if not isinstance(body, dict) or "items" not in body:
                request_result = "failed"
                for idx, ev_id in enumerate(bulk_event_ids):
                    op = bulk_item_ops[idx]
                    failure_classes[idx] = _classify_status_code(resp.status_code if resp is not None else None)
                    outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op=op, result="failed").inc()
                    outbox_es_bulk_item_failures_total.labels(
                        projection=PROJECTION_NAME,
                        op=op,
                        failure_class=failure_classes[idx] or "unknown",
                    ).inc()
                    failure_ids.append(ev_id)
            else:
                items = body.get("items") or []
                if len(items) != len(bulk_event_ids):
                    request_result = "failed"
                    for idx, ev_id in enumerate(bulk_event_ids):
                        op = bulk_item_ops[idx]
                        failure_classes[idx] = "unknown"
                        outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op=op, result="failed").inc()
                        outbox_es_bulk_item_failures_total.labels(
                            projection=PROJECTION_NAME,
                            op=op,
                            failure_class="unknown",
                        ).inc()
                        failure_ids.append(ev_id)
                else:
                    any_failed = False
                    for idx, item in enumerate(items):
                        op = bulk_item_ops[idx]
                        op_key = next(iter(item.keys()), None)
                        meta = item.get(op_key) if op_key else None
                        status = meta.get("status") if isinstance(meta, dict) else None
                        status_int = _try_parse_int(status)

                        is_success = False
                        if status_int is not None:
                            if op == "delete" and status_int in (200, 404):
                                is_success = True
                            elif 200 <= status_int < 300:
                                is_success = True

                        if is_success:
                            outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op=op, result="success").inc()
                            success_ids.append(bulk_event_ids[idx])
                        else:
                            any_failed = True
                            outbox_es_bulk_items_total.labels(projection=PROJECTION_NAME, op=op, result="failed").inc()
                            failure_classes[idx] = _classify_status_code(status_int)
                            outbox_es_bulk_item_failures_total.labels(
                                projection=PROJECTION_NAME,
                                op=op,
                                failure_class=failure_classes[idx] or "unknown",
                            ).inc()
                            failure_ids.append(bulk_event_ids[idx])

                    if resp is not None and resp.status_code >= 400:
                        request_result = "failed"
                    else:
                        request_result = "partial" if any_failed or bool(body.get("errors")) else "success"

            outbox_es_bulk_requests_total.labels(projection=PROJECTION_NAME, result=request_result).inc()

            now = _utc_now()
            success_id_set = set(success_ids)
            failure_id_set = set(failure_ids)

            async with session_factory() as session:
                session = session

                if success_ids:
                    await session.execute(
                        update(SearchOutboxEventModel)
                        .where(
                            SearchOutboxEventModel.id.in_(success_ids),
                            SearchOutboxEventModel.owner == worker_id,
                            SearchOutboxEventModel.status == "processing",
                            SearchOutboxEventModel.lease_until > now,
                        )
                        .values(
                            status="done",
                            processed_at=now,
                            owner=None,
                            lease_until=None,
                            next_retry_at=None,
                            error=None,
                            updated_at=now,
                        )
                    )
                    for idx, ev_id in enumerate(bulk_event_ids):
                        if ev_id in success_id_set:
                            outbox_processed_total.labels(projection=PROJECTION_NAME, op=bulk_outbox_ops[idx]).inc()

                if failure_ids:
                    for idx, ev_id in enumerate(bulk_event_ids):
                        if ev_id not in failure_id_set:
                            continue

                        failure_class = failure_classes[idx] or "unknown"
                        attempts = attempts_by_id.get(ev_id, 0)
                        next_attempt = attempts + 1

                        should_retry = _should_retry_failure_class(failure_class) and next_attempt < max_attempts
                        next_retry_at = None
                        new_status = "failed"

                        if should_retry:
                            delay = _compute_backoff_seconds(
                                attempt=next_attempt,
                                base=base_backoff_seconds,
                                max_backoff=max_backoff_seconds,
                            )
                            next_retry_at = now + timedelta(seconds=delay)
                            new_status = "pending"

                        await session.execute(
                            update(SearchOutboxEventModel)
                            .where(
                                SearchOutboxEventModel.id == ev_id,
                                SearchOutboxEventModel.owner == worker_id,
                                SearchOutboxEventModel.status == "processing",
                                SearchOutboxEventModel.lease_until > now,
                            )
                            .values(
                                status=new_status,
                                owner=None,
                                lease_until=None,
                                attempts=next_attempt,
                                next_retry_at=next_retry_at,
                                error=f"es_bulk_{failure_class}",
                                updated_at=now,
                            )
                        )

                        outbox_failed_total.labels(
                            projection=PROJECTION_NAME,
                            op=bulk_outbox_ops[idx],
                            reason=f"es_{failure_class}",
                        ).inc()

                await session.commit()


def main() -> None:
    asyncio.run(_worker_loop())


if __name__ == "__main__":  # pragma: no cover
    main()
