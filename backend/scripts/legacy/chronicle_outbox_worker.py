"""Chronicle Outbox → chronicle_entries worker.

Continuously pulls unprocessed rows from chronicle_outbox_events and
materializes/updates chronicle_entries derived from chronicle_events.

This is the Chronicle analogue to search_outbox_worker.py, reusing the same
lease/retry/failed/replay/metrics semantics.

Intended usage (repo root):

  export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
  export OUTBOX_WORKER_ID='c1'
  export OUTBOX_METRICS_PORT=9110
  python backend/scripts/chronicle_outbox_worker.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import socket
import sys
import signal
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional
from contextlib import nullcontext

from prometheus_client import Counter, start_http_server
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert

_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# psycopg async cannot run on ProactorEventLoop. Force Selector policy on Windows.
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from infra.database.session import get_session_factory
from infra.database.models.chronicle_models import ChronicleEventModel
from infra.database.models.chronicle_entries_models import ChronicleEntryModel
from infra.database.models.chronicle_outbox_models import ChronicleOutboxEventModel
from infra.observability.outbox_metrics import (
    outbox_failed_total,
    outbox_inflight_events,
    outbox_lag_events,
    outbox_last_success_timestamp_seconds,
    outbox_oldest_age_seconds,
    outbox_processed_total,
    outbox_stuck_processing_events,
    outbox_retry_scheduled_total,
    outbox_terminal_failed_total,
)
from infra.outbox_core.stuck import stuck_processing_predicate
from infra.observability.runtime_endpoints import RuntimeState, start_runtime_http_server

from api.app.config.logging_config import setup_logging
from infra.observability.tracing import extract_context, setup_tracing

setup_logging()


_tracing_enabled = False
try:
    _tracing_enabled = setup_tracing(default_service_name="wordloom-chronicle-outbox-worker")
except Exception:
    pass

_tracer = None
if _tracing_enabled:
    try:
        from opentelemetry import trace as _otel_trace

        _tracer = _otel_trace.get_tracer("wordloom.chronicle_outbox_worker")
    except Exception:
        _tracer = None


def _start_span(name: str, attributes: dict[str, Any], *, context: Any | None = None):
    if _tracer is None:
        return nullcontext()
    if context is None:
        return _tracer.start_as_current_span(
            name,
            attributes=attributes,
            record_exception=True,
            set_status_on_exception=True,
        )
    return _tracer.start_as_current_span(
        name,
        context=context,
        attributes=attributes,
        record_exception=True,
        set_status_on_exception=True,
    )


logger = logging.getLogger(__name__)

PROJECTION_NAME = "chronicle_events_to_entries"

outbox_owner_mismatch_skips_total = Counter(
    "outbox_owner_mismatch_skips_total",
    "Count of outbox events skipped because owner != this worker (race / lost claim)",
    ["projection"],
)


@dataclass(frozen=True)
class _OutboxEventRow:
    id: Any
    entity_type: str
    entity_id: Any
    op: str
    event_version: int
    attempts: int
    traceparent: str | None = None
    tracestate: str | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


def _summarize(event: ChronicleEventModel) -> str:
    if event.block_id:
        return f"{event.event_type} (book={event.book_id}, block={event.block_id})"
    return f"{event.event_type} (book={event.book_id})"


def _get_projection_version() -> int:
    # Default to v1 to match current behavior.
    return _get_int_env("CHRONICLE_PROJECTION_VERSION", _get_int_env("OUTBOX_PROJECTION_VERSION", 1))


def _fault_inject_kind() -> str:
    # Labs-only: optionally inject a synthetic failure for a specific entity_id.
    # Values: "transient" | "deterministic" | "" (disabled)
    return (os.getenv("OUTBOX_FAULT_INJECT_KIND") or "").strip().lower()


def _fault_inject_entity_id() -> str:
    # UUID string expected; compare as string to avoid driver/UUID type differences.
    return (os.getenv("OUTBOX_FAULT_INJECT_ENTITY_ID") or "").strip()


class DeterministicError(Exception):
    pass


async def _sanitize_terminal_rows(session) -> None:
    """Keep terminal rows in a consistent state."""

    now = _utc_now()
    await session.execute(
        update(ChronicleOutboxEventModel)
        .where(
            ChronicleOutboxEventModel.processed_at.is_(None),
            ChronicleOutboxEventModel.status == "failed",
        )
        .values(
            owner=None,
            lease_until=None,
            next_retry_at=None,
            updated_at=now,
        )
    )


async def _reclaim_stuck_processing(session, *, max_processing_seconds: int) -> int:
    now = _utc_now()
    result = await session.execute(
        update(ChronicleOutboxEventModel)
        .where(
            stuck_processing_predicate(
                ChronicleOutboxEventModel,
                now=now,
                max_processing_seconds=max_processing_seconds,
            )
        )
        .values(
            status="pending",
            owner=None,
            lease_until=None,
            processing_started_at=None,
            next_retry_at=None,
            updated_at=now,
        )
    )
    return int(getattr(result, "rowcount", 0) or 0)


async def _claim_batch(session, *, worker_id: str, lease_seconds: int, batch_size: int) -> list[_OutboxEventRow]:
    now = _utc_now()

    claimable = (
        await session.execute(
            select(ChronicleOutboxEventModel)
            .where(
                ChronicleOutboxEventModel.processed_at.is_(None),
                ChronicleOutboxEventModel.status == "pending",
                (
                    ChronicleOutboxEventModel.next_retry_at.is_(None)
                    | (ChronicleOutboxEventModel.next_retry_at <= now)
                ),
            )
            .order_by(ChronicleOutboxEventModel.created_at.asc(), ChronicleOutboxEventModel.id.asc())
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
    ).scalars().all()

    if not claimable:
        return []

    ids = [row.id for row in claimable]
    lease_until = now + timedelta(seconds=int(lease_seconds))
    await session.execute(
        update(ChronicleOutboxEventModel)
        .where(ChronicleOutboxEventModel.id.in_(ids))
        .values(
            status="processing",
            owner=worker_id,
            lease_until=lease_until,
            processing_started_at=now,
            updated_at=now,
            error_reason=None,
            error=None,
        )
    )

    await session.commit()

    return [
        _OutboxEventRow(
            id=row.id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            op=row.op,
            event_version=int(row.event_version or 0),
            attempts=int(row.attempts or 0),
            traceparent=getattr(row, "traceparent", None),
            tracestate=getattr(row, "tracestate", None),
        )
        for row in claimable
    ]


def _compute_next_retry_at(now: datetime, *, attempts: int, base: float, max_backoff: float) -> datetime:
    # Exponential backoff with jitter.
    # attempt=1 -> base
    factor = max(0, attempts)
    backoff = min(max_backoff, base * (2 ** max(0, factor - 1)))
    jitter = random.random() * backoff * 0.2
    return now + timedelta(seconds=(backoff + jitter))


async def _mark_done(session, *, ev_id: Any, worker_id: str) -> None:
    now = _utc_now()
    await session.execute(
        update(ChronicleOutboxEventModel)
        .where(
            ChronicleOutboxEventModel.id == ev_id,
            ChronicleOutboxEventModel.owner == worker_id,
            ChronicleOutboxEventModel.status == "processing",
            ChronicleOutboxEventModel.lease_until > now,
        )
        .values(
            status="done",
            processed_at=now,
            owner=None,
            lease_until=None,
            processing_started_at=None,
            next_retry_at=None,
            error_reason=None,
            error=None,
            updated_at=now,
        )
    )


async def _mark_retry(session, *, ev_id: Any, reason: str, error: str, attempts: int, next_retry_at: datetime) -> None:
    now = _utc_now()
    await session.execute(
        update(ChronicleOutboxEventModel)
        .where(ChronicleOutboxEventModel.id == ev_id)
        .values(
            status="pending",
            owner=None,
            lease_until=None,
            processing_started_at=None,
            attempts=attempts,
            next_retry_at=next_retry_at,
            error_reason=reason,
            error=error[:8000],
            updated_at=now,
        )
    )


async def _mark_failed(session, *, ev_id: Any, reason: str, error: str, attempts: int) -> None:
    now = _utc_now()
    await session.execute(
        update(ChronicleOutboxEventModel)
        .where(ChronicleOutboxEventModel.id == ev_id)
        .values(
            status="failed",
            owner=None,
            lease_until=None,
            processing_started_at=None,
            attempts=attempts,
            next_retry_at=None,
            error_reason=reason,
            error=error[:8000],
            updated_at=now,
        )
    )


async def _process_one(session, row: _OutboxEventRow) -> None:
    inject_id = _fault_inject_entity_id()
    if inject_id and str(row.entity_id) == inject_id:
        kind = _fault_inject_kind()
        if kind == "deterministic":
            raise DeterministicError("Fault injected (deterministic)")
        if kind == "transient":
            raise RuntimeError("Fault injected (transient)")

    if row.op != "upsert":
        raise DeterministicError(f"Unknown outbox op: {row.op!r}")

    ev = (await session.execute(select(ChronicleEventModel).where(ChronicleEventModel.id == row.entity_id))).scalar_one_or_none()
    if ev is None:
        raise DeterministicError(f"Missing chronicle_event: {row.entity_id}")

    now = _utc_now()
    projection_version = _get_projection_version()
    stmt = insert(ChronicleEntryModel).values(
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
    stmt = stmt.on_conflict_do_update(
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
    await session.execute(stmt)


async def _update_metrics(session) -> None:
    # Lag: pending + processing (unprocessed)
    pending_count = (
        await session.execute(
            select(func.count()).select_from(ChronicleOutboxEventModel).where(
                ChronicleOutboxEventModel.processed_at.is_(None),
                ChronicleOutboxEventModel.status.in_(["pending", "processing", "failed"]),
            )
        )
    ).scalar_one()

    oldest_created = (
        await session.execute(
            select(func.min(ChronicleOutboxEventModel.created_at)).where(
                ChronicleOutboxEventModel.processed_at.is_(None),
                ChronicleOutboxEventModel.status.in_(["pending", "processing", "failed"]),
            )
        )
    ).scalar_one()

    inflight = (
        await session.execute(
            select(func.count()).select_from(ChronicleOutboxEventModel).where(
                ChronicleOutboxEventModel.processed_at.is_(None),
                ChronicleOutboxEventModel.status == "processing",
            )
        )
    ).scalar_one()

    outbox_lag_events.labels(projection=PROJECTION_NAME).set(int(pending_count or 0))
    outbox_inflight_events.labels(projection=PROJECTION_NAME).set(int(inflight or 0))

    if oldest_created is None:
        outbox_oldest_age_seconds.labels(projection=PROJECTION_NAME).set(0)
    else:
        age = max(0.0, (_utc_now() - oldest_created).total_seconds())
        outbox_oldest_age_seconds.labels(projection=PROJECTION_NAME).set(age)

    stuck = (
        await session.execute(
            select(func.count()).select_from(ChronicleOutboxEventModel).where(
                ChronicleOutboxEventModel.processed_at.is_(None),
                stuck_processing_predicate(
                    ChronicleOutboxEventModel,
                    now=_utc_now(),
                    max_processing_seconds=_get_int_env("OUTBOX_MAX_PROCESSING_SECONDS", 600),
                ),
            )
        )
    ).scalar_one()
    outbox_stuck_processing_events.labels(projection=PROJECTION_NAME).set(int(stuck or 0))


async def _db_ping(session_factory, *, timeout_seconds: float) -> tuple[bool, str | None]:
    async def _do_ping() -> None:
        async with session_factory() as session:
            await session.execute(select(1))
            await session.commit()

    try:
        await asyncio.wait_for(_do_ping(), timeout=timeout_seconds)
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}".strip(": ")


async def _release_processing_rows(
    session_factory,
    *,
    ids: list[Any],
    worker_id: str,
) -> int:
    if not ids:
        return 0
    now = _utc_now()
    async with session_factory() as session:
        result = await session.execute(
            update(ChronicleOutboxEventModel)
            .where(
                ChronicleOutboxEventModel.id.in_(ids),
                ChronicleOutboxEventModel.processed_at.is_(None),
                ChronicleOutboxEventModel.status == "processing",
                ChronicleOutboxEventModel.owner == worker_id,
            )
            .values(
                status="pending",
                owner=None,
                lease_until=None,
                processing_started_at=None,
                next_retry_at=None,
                updated_at=now,
            )
        )
        await session.commit()
        return int(getattr(result, "rowcount", 0) or 0)


async def main_async() -> int:
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must be set")

    worker_id = os.getenv("OUTBOX_WORKER_ID") or socket.gethostname()
    metrics_port = _get_int_env("OUTBOX_METRICS_PORT", 9110)
    http_port = _get_int_env("OUTBOX_HTTP_PORT", metrics_port + 2)

    poll_interval = _get_float_env("OUTBOX_POLL_INTERVAL_SECONDS", 0.2)
    # Keep batch-size knob consistent across projections.
    # Preferred: OUTBOX_BATCH_SIZE (historic for chronicle worker)
    # Alias: OUTBOX_BULK_SIZE (used by search worker)
    batch_size = _get_int_env("OUTBOX_BATCH_SIZE", _get_int_env("OUTBOX_BULK_SIZE", 50))
    lease_seconds = _get_int_env("OUTBOX_LEASE_SECONDS", 30)
    reclaim_interval_seconds = _get_float_env("OUTBOX_RECLAIM_INTERVAL_SECONDS", 5.0)
    max_processing_seconds = _get_int_env("OUTBOX_MAX_PROCESSING_SECONDS", 600)
    run_seconds = _get_float_env("OUTBOX_RUN_SECONDS", 0.0)

    shutdown_grace_seconds = _get_float_env("OUTBOX_SHUTDOWN_GRACE_SECONDS", 25.0)
    health_max_silence_seconds = _get_float_env("OUTBOX_HEALTH_MAX_SILENCE_SECONDS", 10.0)
    db_ping_timeout_seconds = _get_float_env("OUTBOX_DB_PING_TIMEOUT_SECONDS", 1.0)
    db_ping_interval_seconds = _get_float_env("OUTBOX_DB_PING_INTERVAL_SECONDS", 1.0)
    db_fails_before_draining = _get_int_env("OUTBOX_DB_PING_FAILS_BEFORE_DRAINING", 3)

    max_attempts = _get_int_env("OUTBOX_MAX_ATTEMPTS", 10)
    base_backoff = _get_float_env("OUTBOX_BASE_BACKOFF_SECONDS", 0.5)
    max_backoff = _get_float_env("OUTBOX_MAX_BACKOFF_SECONDS", 10.0)

    start_http_server(metrics_port)
    logger.info(f"[chronicle worker] metrics on :{metrics_port}")

    runtime = RuntimeState(projection=PROJECTION_NAME, worker_id=str(worker_id))
    try:
        start_runtime_http_server(
            port=http_port,
            state=runtime,
            health_max_silence_seconds=health_max_silence_seconds,
        )
        logger.info("[chronicle worker] runtime endpoints on :%s (/healthz,/readyz)", http_port)
    except Exception:  # noqa: BLE001
        logger.exception("[chronicle worker] Failed to start runtime HTTP server on :%s", http_port)

    session_factory = await get_session_factory()

    # Initialize metrics to 0.
    outbox_lag_events.labels(projection=PROJECTION_NAME).set(0)
    outbox_oldest_age_seconds.labels(projection=PROJECTION_NAME).set(0)
    outbox_inflight_events.labels(projection=PROJECTION_NAME).set(0)

    started_mono = time.monotonic()
    last_reclaim_at = 0.0
    last_db_ping_at = 0.0
    stop_requested_at_mono: float | None = None

    def _request_stop(reason: str) -> None:
        nonlocal stop_requested_at_mono
        runtime.request_stop(reason)
        if stop_requested_at_mono is None:
            stop_requested_at_mono = time.monotonic()

    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, lambda: _request_stop("SIGTERM"))
        loop.add_signal_handler(signal.SIGINT, lambda: _request_stop("SIGINT"))
    except Exception:
        try:
            signal.signal(signal.SIGTERM, lambda _s, _f: _request_stop("SIGTERM"))
            signal.signal(signal.SIGINT, lambda _s, _f: _request_stop("SIGINT"))
        except Exception:
            # Signal handling may be unsupported (e.g., embedded environments).
            pass

    while True:
        with _start_span(
            "outbox_worker.loop",
            {
                "projection": "chronicle",
                "wordloom.projection": PROJECTION_NAME,
                "wordloom.worker.id": str(worker_id),
            },
        ):
            runtime.mark_loop_tick()

        if run_seconds > 0 and (time.monotonic() - started_mono) >= run_seconds:
            logger.info("[chronicle worker] exiting after OUTBOX_RUN_SECONDS=%s", run_seconds)
            runtime.set_state("STOPPED")
            return 0

        if stop_requested_at_mono is not None and (time.monotonic() - stop_requested_at_mono) >= shutdown_grace_seconds:
            logger.warning(
                "[chronicle worker] shutdown grace exceeded (%ss); exiting",
                shutdown_grace_seconds,
            )
            runtime.set_state("STOPPED")
            return 0

        try:
            now_mono = time.monotonic()

            # Guardrail: DB ping + readiness.
            if db_ping_interval_seconds > 0 and (now_mono - last_db_ping_at) >= db_ping_interval_seconds:
                ok, err = await _db_ping(session_factory, timeout_seconds=db_ping_timeout_seconds)
                runtime.set_db_check(ok=ok, error=err)
                last_db_ping_at = now_mono
                snap = runtime.snapshot()
                if not ok and snap.consecutive_db_failures >= db_fails_before_draining:
                    runtime.set_state("DRAINING")
                elif ok and (not snap.stop_requested):
                    runtime.set_state("RUNNING")

            if reclaim_interval_seconds > 0 and (now_mono - last_reclaim_at) >= reclaim_interval_seconds:
                async with session_factory() as session:
                    await _sanitize_terminal_rows(session)
                    reclaimed = await _reclaim_stuck_processing(session, max_processing_seconds=max_processing_seconds)
                    if reclaimed:
                        logger.info("Reclaimed %s stuck chronicle outbox events", reclaimed)
                    await session.commit()
                last_reclaim_at = now_mono

            async with session_factory() as session:
                await _update_metrics(session)
                await session.commit()

            # Stop claiming new work once stop is requested or while draining due to guardrails.
            snap = runtime.snapshot()
            if snap.stop_requested or snap.state == "DRAINING" or (not snap.last_db_ok):
                if snap.stop_requested:
                    logger.info("[chronicle worker] stop requested; not claiming new work")
                await asyncio.sleep(min(1.0, max(0.1, poll_interval)))
                if snap.stop_requested:
                    runtime.set_state("STOPPED")
                    return 0
                continue

            with _start_span(
                "outbox.claim_batch",
                {
                    "projection": "chronicle",
                    "wordloom.projection": PROJECTION_NAME,
                    "wordloom.worker.id": str(worker_id),
                    "batch_size": int(batch_size),
                },
            ) as claim_span:
                async with session_factory() as session:
                    events = await _claim_batch(
                        session,
                        worker_id=worker_id,
                        lease_seconds=lease_seconds,
                        batch_size=batch_size,
                    )
                if claim_span is not None:
                    try:
                        claim_span.set_attribute("claimed", int(len(events or [])))
                    except Exception:
                        pass

            logger.info(
                {
                    "event": "outbox.claim_batch",
                    "layer": "worker",
                    "projection": PROJECTION_NAME,
                    "worker_id": str(worker_id),
                    "batch_size": int(batch_size),
                    "claimed": int(len(events or [])),
                }
            )

            if not events:
                await asyncio.sleep(poll_interval)
                continue

            attempt_max = max((int(getattr(e, "attempts", 0) or 0) for e in events), default=0)

            ops = {str(getattr(e, "op", None) or "unknown") for e in events}
            entity_types = {str(getattr(e, "entity_type", None) or "unknown") for e in events}
            batch_op = next(iter(ops)) if len(ops) == 1 else "mixed"
            batch_entity_type = next(iter(entity_types)) if len(entity_types) == 1 else "mixed"

            batch_parent_ctx = None
            try:
                traceparents = {e.traceparent for e in events if getattr(e, "traceparent", None)}
                tracestates = {e.tracestate for e in events if getattr(e, "tracestate", None)}
                if len(traceparents) == 1 and len(tracestates) <= 1:
                    batch_parent_ctx = extract_context(
                        traceparent=next(iter(traceparents)),
                        tracestate=(next(iter(tracestates)) if tracestates else None),
                    )
            except Exception:
                batch_parent_ctx = None

            with _start_span(
                "projection.process_batch",
                {
                    "projection": "chronicle",
                    "wordloom.projection": PROJECTION_NAME,
                    "batch_size": int(len(events)),
                    "attempt": int(attempt_max),
                    "op": batch_op,
                    "entity_type": batch_entity_type,
                },
                context=batch_parent_ctx,
            ) as batch_span:
                for idx, ev in enumerate(events):
                    if stop_requested_at_mono is not None and (time.monotonic() - stop_requested_at_mono) >= shutdown_grace_seconds:
                        remaining_ids = [e.id for e in events[idx:]]
                        try:
                            released = await _release_processing_rows(
                                session_factory,
                                ids=remaining_ids,
                                worker_id=worker_id,
                            )
                            if released:
                                logger.warning(
                                    "[chronicle worker] shutdown deadline hit; released %s/%s claimed rows",
                                    released,
                                    len(remaining_ids),
                                )
                        except Exception:
                            logger.exception("[chronicle worker] Failed to release claimed rows during shutdown")
                        if batch_span is not None:
                            try:
                                batch_span.set_attribute("result", "failed")
                            except Exception:
                                pass
                        runtime.set_state("STOPPED")
                        return 0

                    async with session_factory() as session:
                        try:
                            # Reload row to confirm ownership/lease before doing work.
                            db_ev = (
                                await session.execute(
                                    select(ChronicleOutboxEventModel).where(ChronicleOutboxEventModel.id == ev.id)
                                )
                            ).scalar_one_or_none()

                            if db_ev is None:
                                await session.commit()
                                continue

                            now = _utc_now()
                            if db_ev.processed_at is not None:
                                await session.commit()
                                continue
                            if db_ev.status != "processing" or db_ev.owner != worker_id:
                                if db_ev.owner != worker_id:
                                    outbox_owner_mismatch_skips_total.labels(projection=PROJECTION_NAME).inc()
                                await session.commit()
                                continue
                            if db_ev.lease_until is None or db_ev.lease_until <= now:
                                await session.commit()
                                continue

                            try:
                                with _start_span(
                                    "outbox.process",
                                    {
                                        "wordloom.projection": PROJECTION_NAME,
                                        "wordloom.outbox.id": str(ev.id),
                                        "wordloom.entity.type": str(ev.entity_type),
                                        "wordloom.entity.id": str(ev.entity_id),
                                        "wordloom.outbox.op": str(ev.op),
                                        "wordloom.outbox.event_version": int(ev.event_version or 0),
                                        "wordloom.outbox.attempts": int(ev.attempts or 0),
                                    },
                                ):
                                    await _process_one(session, ev)

                                await _mark_done(session, ev_id=ev.id, worker_id=worker_id)
                                outbox_processed_total.labels(projection=PROJECTION_NAME, op=str(db_ev.op)).inc()
                                outbox_last_success_timestamp_seconds.labels(projection=PROJECTION_NAME).set(now.timestamp())
                            except DeterministicError as exc:
                                attempts = int(getattr(ev, "attempts", 0) or 0) + 1
                                await _mark_failed(
                                    session,
                                    ev_id=ev.id,
                                    reason="deterministic_exception",
                                    error=str(exc),
                                    attempts=attempts,
                                )
                                outbox_terminal_failed_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=str(db_ev.op),
                                    reason="deterministic_exception",
                                ).inc()
                                outbox_failed_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=str(db_ev.op),
                                    reason="deterministic_exception",
                                ).inc()
                            except Exception as exc:
                                attempts = int(getattr(ev, "attempts", 0) or 0) + 1
                                if attempts >= max_attempts:
                                    await _mark_failed(
                                        session,
                                        ev_id=ev.id,
                                        reason="unknown_exception",
                                        error=str(exc),
                                        attempts=attempts,
                                    )
                                    outbox_terminal_failed_total.labels(
                                        projection=PROJECTION_NAME,
                                        op=str(db_ev.op),
                                        reason="unknown_exception",
                                    ).inc()
                                else:
                                    next_retry_at = _compute_next_retry_at(
                                        _utc_now(),
                                        attempts=attempts,
                                        base=base_backoff,
                                        max_backoff=max_backoff,
                                    )
                                    await _mark_retry(
                                        session,
                                        ev_id=ev.id,
                                        reason="unknown_exception",
                                        error=str(exc),
                                        attempts=attempts,
                                        next_retry_at=next_retry_at,
                                    )
                                    outbox_retry_scheduled_total.labels(
                                        projection=PROJECTION_NAME,
                                        op=str(db_ev.op),
                                        reason="unknown_exception",
                                    ).inc()

                                outbox_failed_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=str(db_ev.op),
                                    reason="unknown_exception",
                                ).inc()

                            await session.commit()
                        except Exception:
                            logger.exception("[chronicle worker] Failed to process outbox event %s", ev.id)
                            await session.rollback()

                if batch_span is not None:
                    try:
                        batch_span.set_attribute("result", "ok")
                    except Exception:
                        pass

            logger.info(
                {
                    "event": "projection.process_batch",
                    "layer": "worker",
                    "projection": PROJECTION_NAME,
                    "worker_id": str(worker_id),
                    "batch_size": int(len(events)),
                    "attempt": int(attempt_max),
                    "op": batch_op,
                    "entity_type": batch_entity_type,
                    "result": "ok",
                }
            )

        except Exception:
            logger.exception("[chronicle worker] loop error")
            await asyncio.sleep(1.0)


def main() -> None:
    if sys.platform == "win32":
        # psycopg async is incompatible with ProactorEventLoop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":  # pragma: no cover
    main()
