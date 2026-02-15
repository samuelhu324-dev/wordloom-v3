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
import signal
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from pathlib import Path
from dataclasses import dataclass
from contextlib import nullcontext

import httpx
from prometheus_client import Counter, start_http_server
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend root is on sys.path so `infra.*` imports work whether this
# script is run from the repo root (python backend/scripts/...) or from
# backend/ directly (python scripts/...).
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
from infra.database.models.search_index_models import SearchIndexModel
from infra.database.models.search_outbox_models import SearchOutboxEventModel
from infra.database.models.projection_status_models import ProjectionStatusModel
from infra.observability.outbox_metrics import (
    outbox_failed_total,
    outbox_idempotent_noop_total,
    outbox_inflight_events,
    outbox_lag_events,
    outbox_last_success_timestamp_seconds,
    outbox_oldest_age_seconds,
    outbox_processed_total,
    outbox_stuck_processing_events,
    outbox_retry_scheduled_total,
    outbox_terminal_failed_total,
    projection_rebuild_duration_seconds,
    projection_rebuild_last_finished_timestamp_seconds,
    projection_rebuild_last_success,
    outbox_es_bulk_item_failures_total,
    outbox_es_bulk_items_total,
    outbox_es_bulk_request_duration_seconds,
    outbox_es_bulk_requests_total,
)

from infra.outbox_core.stuck import stuck_processing_predicate
from infra.observability.runtime_endpoints import RuntimeState, start_runtime_http_server

from api.app.config.logging_config import setup_logging
from infra.observability.tracing import extract_context, instrument_httpx, setup_tracing

setup_logging()


_tracing_enabled = False
try:
    _tracing_enabled = setup_tracing(default_service_name="wordloom-search-outbox-worker")
    if _tracing_enabled:
        instrument_httpx()
except Exception as _tracing_exc:
    logger = logging.getLogger(__name__)
    logger.warning({"event": "tracing.setup_failed", "layer": "worker", "error": str(_tracing_exc)})

if not _tracing_enabled:
    logger = logging.getLogger(__name__)
    logger.info(
        {
            "event": "tracing.disabled",
            "layer": "worker",
            "WORDLOOM_TRACING_ENABLED": (os.getenv("WORDLOOM_TRACING_ENABLED") or "").strip(),
            "OTEL_SDK_DISABLED": (os.getenv("OTEL_SDK_DISABLED") or "").strip(),
        }
    )

_tracer = None
if _tracing_enabled:
    try:
        from opentelemetry import trace as _otel_trace

        _tracer = _otel_trace.get_tracer("wordloom.search_outbox_worker")
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

PROJECTION_NAME = "search_index_to_elastic"

# Observability schema marker: helps distinguish traces emitted by different
# versions of this worker during iterative Labs runs.
OBS_SCHEMA_VERSION = "labs-009-v2"


# Labs-only observability: count and sample-log race-induced skips.
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
    claim_batch_id: str | None = None
    traceparent: str | None = None
    tracestate: str | None = None


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


def _get_optional_float_env(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid float env {name}={raw!r}") from exc


def _get_optional_int_env(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid int env {name}={raw!r}") from exc


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


def _is_deterministic_exception(exc: Exception) -> bool:
    # Heuristic: common programming/data errors won't be fixed by retry.
    return isinstance(exc, (ValueError, KeyError, TypeError))


def _classify_attempt_outcome(exc: Exception) -> tuple[str, bool]:
    """Return (reason, retryable) for a processing exception.

    This worker talks to Elasticsearch via HTTPX, so we intentionally emit
    low-cardinality `es_*` reasons suitable for aggregation.

    v2 default is fail-safe: unknown exceptions are treated as retryable unless
    they look deterministic.
    """

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if status_code == 429:
            return "es_429", True
        if 500 <= status_code < 600:
            return "es_5xx", True
        if 400 <= status_code < 500:
            return "es_4xx", False
        return "es_other", True

    if isinstance(exc, httpx.TimeoutException):
        return "es_timeout", True
    if isinstance(exc, httpx.ConnectError):
        return "es_connect", True
    if isinstance(exc, httpx.RequestError):
        return "es_request_error", True

    if _is_deterministic_exception(exc):
        return "deterministic_exception", False

    return "unknown_exception", True


def _format_error(exc: Exception) -> str:
    msg = str(exc).strip()
    if msg:
        return f"{type(exc).__name__}: {msg}"
    return f"{type(exc).__name__}"


def _is_transient_reason(reason: str) -> bool:
    # Transient dependency failures should not become terminal just because ES
    # was down for a few minutes.
    return reason in {
        "es_429",
        "es_5xx",
        "es_timeout",
        "es_connect",
        "es_request_error",
        "es_unknown",
        "es_other",
    }


def _classify_bulk_item_failure(*, status_code: int | None) -> tuple[str, bool]:
    if status_code is None:
        return "es_unknown", True
    if status_code == 429:
        return "es_429", True
    if 500 <= status_code < 600:
        return "es_5xx", True
    if 400 <= status_code < 500:
        return "es_4xx", False
    return "es_other", True


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
        "library_id": (str(row.library_id) if getattr(row, "library_id", None) else None),
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
    if resp.status_code == 404:
        outbox_idempotent_noop_total.labels(projection=PROJECTION_NAME, op="delete", reason="es_404").inc()
        try:
            from opentelemetry import trace as _otel_trace

            span = _otel_trace.get_current_span()
            if span is not None and getattr(span, "is_recording", lambda: False)():
                span.set_attribute("wordloom.idempotent_noop", True)
                span.set_attribute("wordloom.idempotent_noop_reason", "es_404")
        except Exception:
            pass
        logger.info("Outbox delete: doc %s not found in ES (noop)", doc_id)
    else:
        logger.info("Outbox delete: deleted %s from ES", doc_id)


async def _worker_loop() -> None:
    db_url = os.getenv("DATABASE_URL")
    es_url = (os.getenv("ELASTIC_URL") or "http://localhost:9200").strip().rstrip("/")
    es_index = (os.getenv("ELASTIC_INDEX") or "wordloom-search-index").strip()
    metrics_port = int(os.getenv("OUTBOX_METRICS_PORT", "9108"))
    http_port = _get_int_env("OUTBOX_HTTP_PORT", metrics_port + 2)

    # Tuning knobs (Phase 1: make throughput/lag observable & adjustable)
    # Keep batch-size knob consistent across projections.
    # Preferred: OUTBOX_BULK_SIZE (historic for search worker)
    # Alias: OUTBOX_BATCH_SIZE (used by chronicle worker)
    batch_size = _get_int_env("OUTBOX_BULK_SIZE", _get_int_env("OUTBOX_BATCH_SIZE", 100))
    concurrency = _get_int_env("OUTBOX_CONCURRENCY", 1)
    poll_interval_seconds = _get_float_env("OUTBOX_POLL_INTERVAL_SECONDS", 1.0)
    use_es_bulk_api = _get_bool_env("OUTBOX_USE_ES_BULK", False)

    # Labs knobs: deterministic fault injection for Experiment B (ES 429).
    # Disabled by default.
    fault_es_429_ratio = _get_float_env("OUTBOX_EXPERIMENT_ES_429_RATIO", 0.0)
    fault_es_429_every_n = _get_optional_int_env("OUTBOX_EXPERIMENT_ES_429_EVERY_N")
    fault_es_429_ops_raw = (os.getenv("OUTBOX_EXPERIMENT_ES_429_OPS") or "").strip()
    fault_es_429_ops = {
        p.strip().lower()
        for p in fault_es_429_ops_raw.split(",")
        if p.strip()
    }
    fault_es_429_seed = _get_optional_int_env("OUTBOX_EXPERIMENT_ES_429_SEED")
    fault_es_429_rng = random.Random(fault_es_429_seed)
    fault_es_429_counter = 0

    # Labs knobs: force ES bulk partial success (Experiment D).
    # Disabled by default; meaningful only when OUTBOX_USE_ES_BULK=1 and bulk has >=2 items.
    fault_es_bulk_partial_enabled = _get_bool_env("OUTBOX_EXPERIMENT_ES_BULK_PARTIAL", False)
    fault_es_bulk_partial_status = _get_int_env("OUTBOX_EXPERIMENT_ES_BULK_PARTIAL_STATUS", 400)

    # Labs knobs: intentionally break claim atomicity (Experiment B1).
    # Default is off to preserve production behavior.
    break_claim_atomicity = _get_bool_env("OUTBOX_EXPERIMENT_BREAK_CLAIM", False)
    break_claim_sleep_seconds = _get_optional_float_env("OUTBOX_EXPERIMENT_BREAK_CLAIM_SLEEP_SECONDS")
    if break_claim_sleep_seconds is None:
        break_claim_sleep_seconds = 0.2

    # Labs knobs: intentionally slow processing after claim (Experiment F).
    # Disabled by default.
    process_sleep_seconds = _get_optional_float_env("OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS")
    if process_sleep_seconds is None:
        process_sleep_seconds = 0.0

    worker_id = os.getenv("OUTBOX_WORKER_ID")
    if not worker_id:
        worker_id = f"{socket.gethostname()}:{os.getpid()}"

    lease_seconds = _get_int_env("OUTBOX_LEASE_SECONDS", 30)
    max_processing_seconds = _get_int_env("OUTBOX_MAX_PROCESSING_SECONDS", max(300, lease_seconds * 10))
    max_attempts = _get_int_env("OUTBOX_MAX_ATTEMPTS", 10)
    terminal_on_transient = _get_bool_env("OUTBOX_TERMINAL_ON_TRANSIENT", False)
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

    if not es_url:
        raise RuntimeError(
            "ELASTIC_URL is empty. Fix by setting ELASTIC_URL (e.g. http://localhost:9200) or unsetting it to use the default."
        )
    if not (es_url.startswith("http://") or es_url.startswith("https://")):
        raise RuntimeError(
            f"ELASTIC_URL must include scheme (http:// or https://). Got: {es_url!r}"
        )
    if not es_index:
        raise RuntimeError(
            "ELASTIC_INDEX is empty. Fix by setting ELASTIC_INDEX (e.g. wordloom-test-search-index) or unsetting it to use the default."
        )

    logger.info(
        "Search outbox worker starting: db=%s, es=%s index=%s, bulk=%s, concurrency=%s, poll=%.3fs, worker_id=%s, lease=%ss, max_processing=%ss",
        db_url,
        es_url,
        es_index,
        batch_size,
        concurrency,
        poll_interval_seconds,
        worker_id,
        lease_seconds,
        max_processing_seconds,
    )
    logger.info(
        "Observability schema: %s (file=%s)",
        OBS_SCHEMA_VERSION,
        str(_HERE),
    )

    fault_es_429_mode = "disabled"
    fault_es_429_effective_ratio = 0.0
    if fault_es_429_every_n is not None and fault_es_429_every_n > 0:
        fault_es_429_mode = "every_n"
        fault_es_429_effective_ratio = 1.0 / float(fault_es_429_every_n)
    elif fault_es_429_ratio > 0.0:
        fault_es_429_mode = "ratio"
        fault_es_429_effective_ratio = float(fault_es_429_ratio)

    if fault_es_429_mode != "disabled":
        logger.warning(
            "[LABS] ES 429 fault injection enabled: mode=%s effective_ratio=%.3f ratio=%.3f every_n=%s ops=%s seed=%s",
            fault_es_429_mode,
            float(fault_es_429_effective_ratio),
            float(fault_es_429_ratio),
            str(fault_es_429_every_n),
            (sorted(fault_es_429_ops) if fault_es_429_ops else "<all>"),
            str(fault_es_429_seed),
        )

    if fault_es_bulk_partial_enabled:
        logger.warning(
            "[LABS] ES bulk partial fault injection enabled: status=%s (requires OUTBOX_USE_ES_BULK=1 and >=2 items)",
            int(fault_es_bulk_partial_status),
        )

    if break_claim_atomicity:
        logger.warning(
            "[LABS] OUTBOX_EXPERIMENT_BREAK_CLAIM enabled: claim is non-atomic (no row lock) with %.3fs delay",
            float(break_claim_sleep_seconds),
        )

    if process_sleep_seconds and float(process_sleep_seconds) > 0:
        logger.warning(
            "[LABS] OUTBOX_EXPERIMENT_PROCESS_SLEEP_SECONDS enabled: sleeping %.3fs after claim before processing",
            float(process_sleep_seconds),
        )

    owner_mismatch_skip_count = 0
    last_owner_mismatch_log_at = 0.0

    if use_es_bulk_api and concurrency != 1:
        logger.info("OUTBOX_USE_ES_BULK enabled: OUTBOX_CONCURRENCY is ignored (bulk uses one request per poll)")

    # Expose Prometheus metrics for this worker process.
    start_http_server(metrics_port)
    logger.info("Outbox worker metrics listening on :%s", metrics_port)

    shutdown_grace_seconds = _get_float_env("OUTBOX_SHUTDOWN_GRACE_SECONDS", 25.0)
    health_max_silence_seconds = _get_float_env("OUTBOX_HEALTH_MAX_SILENCE_SECONDS", 10.0)
    db_ping_timeout_seconds = _get_float_env("OUTBOX_DB_PING_TIMEOUT_SECONDS", 1.0)
    db_ping_interval_seconds = _get_float_env("OUTBOX_DB_PING_INTERVAL_SECONDS", 1.0)
    db_fails_before_draining = _get_int_env("OUTBOX_DB_PING_FAILS_BEFORE_DRAINING", 3)
    require_es_ready = _get_bool_env("OUTBOX_REQUIRE_ES_READY", False)
    es_ping_timeout_seconds = _get_float_env("OUTBOX_ES_PING_TIMEOUT_SECONDS", 1.0)
    es_ping_interval_seconds = _get_float_env("OUTBOX_ES_PING_INTERVAL_SECONDS", 1.0)

    # Pre-warm metric series so they show up even when zero.
    outbox_processed_total.labels(projection=PROJECTION_NAME, op="upsert").inc(0)
    outbox_processed_total.labels(projection=PROJECTION_NAME, op="delete").inc(0)
    outbox_idempotent_noop_total.labels(projection=PROJECTION_NAME, op="delete", reason="es_404").inc(0)
    outbox_failed_total.labels(projection=PROJECTION_NAME, op="upsert", reason="none").inc(0)
    outbox_failed_total.labels(projection=PROJECTION_NAME, op="delete", reason="none").inc(0)
    outbox_retry_scheduled_total.labels(projection=PROJECTION_NAME, op="upsert", reason="none").inc(0)
    outbox_retry_scheduled_total.labels(projection=PROJECTION_NAME, op="delete", reason="none").inc(0)
    outbox_terminal_failed_total.labels(projection=PROJECTION_NAME, op="upsert", reason="none").inc(0)
    outbox_terminal_failed_total.labels(projection=PROJECTION_NAME, op="delete", reason="none").inc(0)
    outbox_lag_events.labels(projection=PROJECTION_NAME).set(0)
    outbox_oldest_age_seconds.labels(projection=PROJECTION_NAME).set(0)
    outbox_inflight_events.labels(projection=PROJECTION_NAME).set(0)
    outbox_stuck_processing_events.labels(projection=PROJECTION_NAME).set(0)
    outbox_last_success_timestamp_seconds.labels(projection=PROJECTION_NAME).set(0)
    projection_rebuild_duration_seconds.labels(projection=PROJECTION_NAME).set(0)
    projection_rebuild_last_finished_timestamp_seconds.labels(projection=PROJECTION_NAME).set(0)
    projection_rebuild_last_success.labels(projection=PROJECTION_NAME).set(0)

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

    runtime = RuntimeState(projection=PROJECTION_NAME, worker_id=str(worker_id))

    dep_lock = threading.Lock()
    es_ready_ok = True
    es_ready_reason: str | None = None

    def _extra_ready() -> tuple[bool, str | None]:
        if not require_es_ready:
            return True, None
        with dep_lock:
            return bool(es_ready_ok), es_ready_reason

    try:
        start_runtime_http_server(
            port=http_port,
            state=runtime,
            health_max_silence_seconds=health_max_silence_seconds,
            extra_ready_predicate=_extra_ready,
        )
        logger.info("Outbox runtime endpoints listening on :%s (/healthz,/readyz)", http_port)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to start runtime HTTP server on :%s", http_port)

    # Safety fuse: ensure this worker is pointed at the intended DB.
    expected_env = os.getenv("WORDLOOM_ENV")
    if expected_env:
        from infra.database.env_guard import assert_expected_database_environment

        async with session_factory() as session:
            await assert_expected_database_environment(session)
        logger.info("[ENV_GUARD] Database environment check: OK")

    semaphore = asyncio.Semaphore(concurrency)
    entity_locks: dict[str, asyncio.Lock] = {}
    last_success_timestamp_seconds = 0.0

    last_db_ping_at = 0.0
    last_es_ping_at = 0.0
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
            pass

    async def _db_ping() -> tuple[bool, str | None]:
        async def _do_ping() -> None:
            async with session_factory() as session:
                await session.execute(select(1))
                await session.commit()

        try:
            await asyncio.wait_for(_do_ping(), timeout=db_ping_timeout_seconds)
            return True, None
        except Exception as exc:  # noqa: BLE001
            return False, f"{type(exc).__name__}: {exc}".strip(": ")

    async def _es_ping(client: httpx.AsyncClient) -> tuple[bool, str | None]:
        try:
            resp = await asyncio.wait_for(client.get("/"), timeout=es_ping_timeout_seconds)
            if resp.status_code >= 500:
                return False, f"es_{resp.status_code}"
            return True, None
        except Exception as exc:  # noqa: BLE001
            return False, f"{type(exc).__name__}: {exc}".strip(": ")

    async def _release_processing_rows(ids: list[Any]) -> int:
        if not ids:
            return 0
        now = _utc_now()
        async with session_factory() as session:
            result = await session.execute(
                update(SearchOutboxEventModel)
                .where(
                    SearchOutboxEventModel.id.in_(ids),
                    SearchOutboxEventModel.processed_at.is_(None),
                    SearchOutboxEventModel.status == "processing",
                    SearchOutboxEventModel.owner == worker_id,
                )
                .values(
                    status="pending",
                    owner=None,
                    lease_until=None,
                    processing_started_at=None,
                    next_retry_at=None,
                    error_reason=None,
                    error=None,
                    updated_at=now,
                )
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

    def _remaining_grace_seconds() -> float | None:
        if stop_requested_at_mono is None:
            return None
        return max(0.0, shutdown_grace_seconds - (time.monotonic() - stop_requested_at_mono))

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
                    (
                        SearchOutboxEventModel.owner.is_not(None)
                        | SearchOutboxEventModel.lease_until.is_not(None)
                        | SearchOutboxEventModel.processing_started_at.is_not(None)
                    ),
                )
                .values(
                    owner=None,
                    lease_until=None,
                    processing_started_at=None,
                    updated_at=now,
                )
            )
            await session.commit()
            fixed = int(getattr(result, "rowcount", 0) or 0)
            if fixed:
                logger.warning("Sanitized %s terminal outbox rows with stray owner/lease", fixed)

    async def _reclaim_stuck_processing() -> None:
        if reclaim_interval_seconds <= 0:
            return
        now = _utc_now()
        async with session_factory() as session:
            session = session
            result = await session.execute(
                update(SearchOutboxEventModel)
                .where(stuck_processing_predicate(SearchOutboxEventModel, now=now, max_processing_seconds=max_processing_seconds))
                .values(
                    status="pending",
                    owner=None,
                    lease_until=None,
                    processing_started_at=None,
                    updated_at=now,
                )
            )
            await session.commit()
            reclaimed = int(getattr(result, "rowcount", 0) or 0)
            if reclaimed:
                logger.warning(
                    "Reclaimed %s stuck outbox events (expired lease or max processing exceeded)",
                    reclaimed,
                )

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

    async def _process_one(ev: _OutboxEventRow, client: httpx.AsyncClient) -> tuple[str, str]:
        nonlocal owner_mismatch_skip_count
        nonlocal last_owner_mismatch_log_at
        span_attrs: dict[str, Any] = {
            "wordloom.obs_schema": OBS_SCHEMA_VERSION,
            "wordloom.projection": PROJECTION_NAME,
            "wordloom.worker_id": str(worker_id),
            "wordloom.outbox_event_id": str(ev.id),
            "wordloom.entity_type": str(ev.entity_type),
            "wordloom.entity_id": str(ev.entity_id),
            "wordloom.outbox_op": str(ev.op),
            "wordloom.outbox_event_version": int(ev.event_version or 0),
            "wordloom.outbox_attempts": int(ev.attempts or 0),
            "wordloom.es_index": str(es_index),
            "wordloom.labs.es_429.mode": str(fault_es_429_mode),
            "wordloom.labs.es_429.ratio": float(fault_es_429_ratio),
            "wordloom.labs.es_429.every_n": int(fault_es_429_every_n or 0),
        }
        if fault_es_429_ops:
            span_attrs["wordloom.labs.es_429.ops"] = ",".join(sorted(fault_es_429_ops))
        if fault_es_429_seed is not None:
            span_attrs["wordloom.labs.es_429.seed"] = int(fault_es_429_seed)
        if ev.claim_batch_id:
            span_attrs["wordloom.claim_batch_id"] = str(ev.claim_batch_id)

        with _start_span(
            "outbox.process",
            span_attrs,
        ):
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
                                    return "ok", "none"

                                now = _utc_now()
                                if db_ev.processed_at is not None:
                                    return "ok", "none"
                                if db_ev.status != "processing" or db_ev.owner != worker_id:
                                    if db_ev.owner != worker_id:
                                        outbox_owner_mismatch_skips_total.labels(projection=PROJECTION_NAME).inc()
                                        if break_claim_atomicity:
                                            owner_mismatch_skip_count += 1
                                            now_mono = time.monotonic()
                                            if (now_mono - last_owner_mismatch_log_at) >= 5.0:
                                                logger.warning(
                                                    "[LABS] Skipped %s outbox events due to owner mismatch (race / lost claim). Latest: id=%s owner=%s",
                                                    owner_mismatch_skip_count,
                                                    str(db_ev.id),
                                                    str(db_ev.owner),
                                                )
                                                last_owner_mismatch_log_at = now_mono
                                    return "ok", "owner_mismatch"
                                if db_ev.lease_until is None or db_ev.lease_until <= now:
                                    # Lease expired; let reclaim handle it.
                                    return "retry", "lease_expired"

                                def _maybe_inject_es_429(op: str) -> None:
                                    nonlocal fault_es_429_counter
                                    if fault_es_429_ratio <= 0.0 and (fault_es_429_every_n is None or fault_es_429_every_n <= 0):
                                        return

                                    op_norm = (op or "").strip().lower()
                                    if fault_es_429_ops and op_norm not in fault_es_429_ops:
                                        return

                                    inject = False
                                    if fault_es_429_every_n is not None and fault_es_429_every_n > 0:
                                        fault_es_429_counter += 1
                                        inject = (fault_es_429_counter % fault_es_429_every_n) == 0
                                    else:
                                        inject = fault_es_429_rng.random() < float(fault_es_429_ratio)

                                    if not inject:
                                        return

                                    try:
                                        from opentelemetry import trace as _otel_trace

                                        span = _otel_trace.get_current_span()
                                        if span is not None and getattr(span, "is_recording", lambda: False)():
                                            span.set_attribute("wordloom.labs.es_429.injected", True)
                                            span.set_attribute("wordloom.labs.es_429.op", str(op_norm))
                                            span.set_attribute("wordloom.labs.es_429.counter", int(fault_es_429_counter))
                                    except Exception:
                                        pass

                                    req = httpx.Request("GET", f"{es_url}/_labs/fault/429")
                                    resp = httpx.Response(429, request=req, text="fault_injection")
                                    raise httpx.HTTPStatusError("Injected 429 (fault injection)", request=req, response=resp)

                                if db_ev.op == "upsert":
                                    _maybe_inject_es_429("upsert")
                                    await _process_upsert(session, client, es_index, ev)
                                elif db_ev.op == "delete":
                                    _maybe_inject_es_429("delete")
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
                                        processing_started_at=None,
                                        next_retry_at=None,
                                        error_reason=None,
                                        error=None,
                                        updated_at=now,
                                    )
                                )
                                await session.commit()

                                outbox_processed_total.labels(projection=PROJECTION_NAME, op=db_ev.op).inc()
                                last_success_timestamp_seconds = time.time()
                                outbox_last_success_timestamp_seconds.labels(projection=PROJECTION_NAME).set(
                                    last_success_timestamp_seconds
                                )
                                return "ok", "none"
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("Failed to process outbox event %s", ev.id)

                            failure_class, _status_code = _classify_exception(exc)
                            reason, is_retryable = _classify_attempt_outcome(exc)
                            attempts = int(getattr(ev, "attempts", 0) or 0)
                            next_attempt = attempts + 1

                            is_transient = _is_transient_reason(reason)
                            allow_retry = is_retryable and _should_retry_failure_class(failure_class)
                            ignore_max_attempts = is_transient and (not terminal_on_transient)
                            should_retry = allow_retry and (ignore_max_attempts or next_attempt < max_attempts)

                            # Prevent unbounded attempt growth if we retry forever on transients.
                            attempts_to_store = min(next_attempt, max_attempts) if ignore_max_attempts else next_attempt

                            now = _utc_now()
                            if should_retry:
                                delay = _compute_backoff_seconds(
                                    attempt=attempts_to_store,
                                    base=base_backoff_seconds,
                                    max_backoff=max_backoff_seconds,
                                )
                                next_retry_at = now + timedelta(seconds=delay)
                                values = {
                                    "status": "pending",
                                    "owner": None,
                                    "lease_until": None,
                                    "processing_started_at": None,
                                    "attempts": attempts_to_store,
                                    "next_retry_at": next_retry_at,
                                    "error_reason": reason,
                                    "error": _format_error(exc),
                                    "updated_at": now,
                                }
                            else:
                                values = {
                                    "status": "failed",
                                    "owner": None,
                                    "lease_until": None,
                                    "processing_started_at": None,
                                    "attempts": attempts_to_store,
                                    "next_retry_at": None,
                                    "error_reason": reason,
                                    "error": _format_error(exc),
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
                                reason=reason,
                            ).inc()

                            if values.get("status") == "pending":
                                outbox_retry_scheduled_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=str(getattr(ev, "op", "unknown")),
                                    reason=reason,
                                ).inc()
                                return "retry", reason
                            else:
                                outbox_terminal_failed_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=str(getattr(ev, "op", "unknown")),
                                    reason=reason,
                                ).inc()
                                return "failed", reason

        # Defensive fallback; should be unreachable.
        return "failed", "unknown"

    async with httpx.AsyncClient(base_url=es_url, timeout=10.0) as client:
        last_reclaim_at = 0.0
        while True:
            with _start_span(
                "outbox_worker.loop",
                {
                    "projection": "search",
                    "wordloom.projection": PROJECTION_NAME,
                    "wordloom.worker.id": str(worker_id),
                },
            ) as loop_span:
                runtime.mark_loop_tick()

            remaining = _remaining_grace_seconds()
            if remaining is not None and remaining <= 0.0:
                logger.warning("Shutdown grace exceeded; exiting")
                runtime.set_state("STOPPED")
                return

            now_mono = time.monotonic()

            # Guardrails: DB ping and (optional) ES ping.
            if db_ping_interval_seconds > 0 and (now_mono - last_db_ping_at) >= db_ping_interval_seconds:
                ok, err = await _db_ping()
                runtime.set_db_check(ok=ok, error=err)
                last_db_ping_at = now_mono
                snap = runtime.snapshot()
                if not ok and snap.consecutive_db_failures >= db_fails_before_draining:
                    runtime.set_state("DRAINING")
                elif ok and (not snap.stop_requested):
                    runtime.set_state("RUNNING")

            if require_es_ready and es_ping_interval_seconds > 0 and (now_mono - last_es_ping_at) >= es_ping_interval_seconds:
                ok, reason = await _es_ping(client)
                with dep_lock:
                    es_ready_ok = ok
                    es_ready_reason = reason
                last_es_ping_at = now_mono

            snap = runtime.snapshot()
            if snap.stop_requested:
                logger.info("Stop requested; draining current work only")

            now_monotonic = time.monotonic()
            if reclaim_interval_seconds > 0 and (now_monotonic - last_reclaim_at) >= reclaim_interval_seconds:
                await _sanitize_terminal_rows()
                await _reclaim_stuck_processing()
                last_reclaim_at = now_monotonic

            # If we're draining (SIGTERM) or dependencies are unhealthy, do not claim new work.
            snap = runtime.snapshot()
            if snap.stop_requested:
                runtime.set_state("STOPPED")
                return
            if snap.state == "DRAINING" or (not snap.last_db_ok):
                await asyncio.sleep(min(1.0, max(0.1, poll_interval_seconds)))
                continue

            # Claim a batch of pending events.
            #
            # Normal behavior: SELECT ... FOR UPDATE SKIP LOCKED to avoid blocking
            # between concurrent workers.
            #
            # Labs Experiment B1: when OUTBOX_EXPERIMENT_BREAK_CLAIM=1, we
            # intentionally remove row locking and add a small delay between
            # SELECT and UPDATE to widen the race window.
            async with session_factory() as session:
                session = session

                now = _utc_now()
                claim_batch_id = str(uuid.uuid4())
                # Low-cardinality projection freshness gauges.
                pending_count = (
                    await session.execute(
                        select(func.count()).select_from(SearchOutboxEventModel).where(
                            SearchOutboxEventModel.processed_at.is_(None),
                            SearchOutboxEventModel.status.in_(["pending", "processing", "failed"]),
                        )
                    )
                ).scalar_one()
                inflight_count = (
                    await session.execute(
                        select(func.count()).select_from(SearchOutboxEventModel).where(
                            SearchOutboxEventModel.processed_at.is_(None),
                            SearchOutboxEventModel.status == "processing",
                        )
                    )
                ).scalar_one()

                stuck_processing_count = (
                    await session.execute(
                        select(func.count()).select_from(SearchOutboxEventModel).where(
                            stuck_processing_predicate(
                                SearchOutboxEventModel,
                                now=now,
                                max_processing_seconds=max_processing_seconds,
                            )
                        )
                    )
                ).scalar_one()
                oldest_created_at = (
                    await session.execute(
                        select(func.min(SearchOutboxEventModel.created_at)).where(
                            SearchOutboxEventModel.processed_at.is_(None),
                            SearchOutboxEventModel.status.in_(["pending", "processing", "failed"]),
                        )
                    )
                ).scalar_one_or_none()

                # Rebuild bookkeeping (optional): if present, export as gauges.
                rebuild_row = (
                    await session.execute(
                        select(ProjectionStatusModel).where(ProjectionStatusModel.projection_name == "search")
                    )
                ).scalar_one_or_none()
                if rebuild_row is not None:
                    duration_s = float(getattr(rebuild_row, "last_rebuild_duration_seconds", 0.0) or 0.0)
                    projection_rebuild_duration_seconds.labels(projection=PROJECTION_NAME).set(duration_s)

                    finished_at = getattr(rebuild_row, "last_rebuild_finished_at", None)
                    finished_ts = float(finished_at.timestamp()) if finished_at is not None else 0.0
                    projection_rebuild_last_finished_timestamp_seconds.labels(projection=PROJECTION_NAME).set(
                        finished_ts
                    )

                    ok = getattr(rebuild_row, "last_rebuild_success", None)
                    projection_rebuild_last_success.labels(projection=PROJECTION_NAME).set(
                        1.0 if ok else 0.0
                    )

                outbox_lag_events.labels(projection=PROJECTION_NAME).set(int(pending_count))
                outbox_inflight_events.labels(projection=PROJECTION_NAME).set(int(inflight_count))
                outbox_stuck_processing_events.labels(projection=PROJECTION_NAME).set(int(stuck_processing_count))
                if oldest_created_at is None:
                    outbox_oldest_age_seconds.labels(projection=PROJECTION_NAME).set(0)
                else:
                    age_s = max(0.0, (now - oldest_created_at).total_seconds())
                    outbox_oldest_age_seconds.labels(projection=PROJECTION_NAME).set(float(age_s))

                with _start_span(
                    "outbox.claim_batch",
                    {
                        "wordloom.obs_schema": OBS_SCHEMA_VERSION,
                        "projection": "search",
                        "wordloom.projection": PROJECTION_NAME,
                        "wordloom.worker.id": str(worker_id),
                        "wordloom.claim_batch_id": claim_batch_id,
                        "batch_size": int(batch_size),
                        "claim_mode": "non_atomic" if break_claim_atomicity else "atomic",
                    },
                ) as claim_span:
                    claimable = (
                        await session.execute(
                            select(SearchOutboxEventModel)
                            .where(
                                SearchOutboxEventModel.processed_at.is_(None),
                                SearchOutboxEventModel.status == "pending",
                                (
                                    SearchOutboxEventModel.next_retry_at.is_(None)
                                    | (SearchOutboxEventModel.next_retry_at <= now)
                                ),
                            )
                            .order_by(SearchOutboxEventModel.event_version.asc())
                            .with_for_update(skip_locked=True)
                            .limit(batch_size)
                        )
                    ).scalars().all()

                    if break_claim_atomicity:
                        # Re-run without row locking to intentionally allow races.
                        claimable = (
                            await session.execute(
                                select(SearchOutboxEventModel)
                                .where(
                                    SearchOutboxEventModel.processed_at.is_(None),
                                    SearchOutboxEventModel.status == "pending",
                                    (
                                        SearchOutboxEventModel.next_retry_at.is_(None)
                                        | (SearchOutboxEventModel.next_retry_at <= now)
                                    ),
                                )
                                .order_by(SearchOutboxEventModel.event_version.asc())
                                .limit(batch_size)
                            )
                        ).scalars().all()

                    if claim_span is not None:
                        try:
                            claim_span.set_attribute("claimed", int(len(claimable or [])))
                        except Exception:
                            pass

                    if claimable:
                        if break_claim_atomicity and break_claim_sleep_seconds > 0:
                            await asyncio.sleep(float(break_claim_sleep_seconds))
                        ids = [row.id for row in claimable]
                        await session.execute(
                            update(SearchOutboxEventModel)
                            .where(SearchOutboxEventModel.id.in_(ids))
                            .values(
                                status="processing",
                                owner=worker_id,
                                lease_until=_lease_until(now),
                                processing_started_at=now,
                                updated_at=now,
                                error_reason=None,
                                error=None,
                            )
                        )
                        await session.commit()
                    else:
                        ids = []

                    logger.info(
                        {
                            "event": "outbox.claim_batch",
                            "layer": "worker",
                            "projection": PROJECTION_NAME,
                            "worker_id": str(worker_id),
                            "claim_batch_id": claim_batch_id,
                            "obs_schema": OBS_SCHEMA_VERSION,
                            "batch_size": int(batch_size),
                            "claimed": int(len(claimable or [])),
                            "claim_mode": "non_atomic" if break_claim_atomicity else "atomic",
                        }
                    )

            if not claimable:
                await asyncio.sleep(poll_interval_seconds)
                continue

            if process_sleep_seconds and float(process_sleep_seconds) > 0:
                await asyncio.sleep(float(process_sleep_seconds))

            events = [
                _OutboxEventRow(
                    id=row.id,
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    op=row.op,
                    event_version=int(row.event_version or 0),
                    attempts=int(row.attempts or 0),
                    claim_batch_id=claim_batch_id,
                    traceparent=getattr(row, "traceparent", None),
                    tracestate=getattr(row, "tracestate", None),
                )
                for row in claimable
            ]

            def _homogeneous_or_mixed(values: list[str]) -> str:
                uniq = {v for v in values if v is not None}
                if len(uniq) == 1:
                    return next(iter(uniq))
                return "mixed"

            batch_op = _homogeneous_or_mixed([str(ev.op) for ev in events])
            batch_entity_type = _homogeneous_or_mixed([str(ev.entity_type) for ev in events])
            attempt_max = max((int(ev.attempts or 0) for ev in events), default=0)

            batch_parent_ctx = None
            try:
                traceparents = {ev.traceparent for ev in events if ev.traceparent}
                tracestates = {ev.tracestate for ev in events if ev.tracestate}
                if len(traceparents) == 1 and len(tracestates) <= 1:
                    batch_parent_ctx = extract_context(
                        traceparent=next(iter(traceparents)),
                        tracestate=(next(iter(tracestates)) if tracestates else None),
                    )
            except Exception:
                batch_parent_ctx = None

            loop_cm = nullcontext()
            if batch_parent_ctx is not None:
                loop_cm = _start_span(
                    "outbox_worker.loop",
                    {
                        "projection": "search",
                        "wordloom.projection": PROJECTION_NAME,
                        "wordloom.worker.id": str(worker_id),
                    },
                    context=batch_parent_ctx,
                )

            # Process a batch with bounded concurrency. Per-entity lock prevents
            # out-of-order writes for the same entity when concurrency > 1.
            with loop_cm:
                if batch_parent_ctx is not None:
                    with _start_span(
                        "outbox.claim_batch",
                        {
                            "projection": "search",
                            "wordloom.projection": PROJECTION_NAME,
                            "wordloom.worker.id": str(worker_id),
                            "batch_size": int(len(events)),
                        },
                    ) as _claim_marker_span:
                        if _claim_marker_span is not None:
                            try:
                                _claim_marker_span.set_attribute("claimed", int(len(events)))
                            except Exception:
                                pass

                if not use_es_bulk_api:
                    batch_span_attrs: dict[str, Any] = {
                        "wordloom.obs_schema": OBS_SCHEMA_VERSION,
                        "projection": "search",
                        "wordloom.projection": PROJECTION_NAME,
                        "wordloom.worker_id": str(worker_id),
                        "wordloom.claim_batch_id": claim_batch_id,
                        "batch_size": int(len(events)),
                        "entity_type": batch_entity_type,
                        "op": batch_op,
                        "attempt": int(attempt_max),
                    }

                    with _start_span(
                        "projection.process_batch",
                        batch_span_attrs,
                    ) as batch_span:
                        tasks = [asyncio.create_task(_process_one(ev, client)) for ev in events]
                        remaining = _remaining_grace_seconds()
                        batch_result = "failed"
                        batch_reason = "unknown"
                        ok_count = 0
                        retry_count = 0
                        failed_count = 0
                        try:
                            results: list[tuple[str, str]]
                            if remaining is None:
                                results = await asyncio.gather(*tasks)
                            else:
                                results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=remaining)

                            ok_count = sum(1 for r, _ in results if r == "ok")
                            retry_count = sum(1 for r, _ in results if r == "retry")
                            failed_count = sum(1 for r, _ in results if r == "failed")

                            if failed_count > 0:
                                batch_result = "failed"
                            elif retry_count > 0:
                                batch_result = "retry"
                            else:
                                batch_result = "ok"

                            reasons = {reason for _r, reason in results if reason and reason != "none"}
                            if not reasons:
                                batch_reason = "none"
                            elif len(reasons) == 1:
                                batch_reason = next(iter(reasons))
                            else:
                                batch_reason = "mixed"

                        except asyncio.TimeoutError:
                            batch_result = "failed"
                            batch_reason = "timeout"
                            for t in tasks:
                                t.cancel()
                            await asyncio.gather(*tasks, return_exceptions=True)
                            try:
                                released = await _release_processing_rows([ev.id for ev in events])
                                logger.warning(
                                    "Shutdown deadline hit; released %s/%s claimed rows",
                                    released,
                                    len(events),
                                )
                            except Exception:  # noqa: BLE001
                                logger.exception("Failed to release claimed rows during shutdown")
                            runtime.set_state("STOPPED")
                            return
                        finally:
                            if batch_span is not None:
                                try:
                                    batch_span.set_attribute("result", batch_result)
                                    batch_span.set_attribute("reason", batch_reason)
                                    batch_span.set_attribute("ok_count", int(ok_count))
                                    batch_span.set_attribute("retry_count", int(retry_count))
                                    batch_span.set_attribute("failed_count", int(failed_count))
                                except Exception:
                                    pass
                                if batch_result == "failed":
                                    try:
                                        from opentelemetry.trace.status import Status, StatusCode

                                        batch_span.set_status(Status(StatusCode.ERROR))
                                    except Exception:
                                        pass

                        logger.info(
                            {
                                "event": "projection.process_batch",
                                "layer": "worker",
                                "projection": PROJECTION_NAME,
                                "worker_id": str(worker_id),
                                "claim_batch_id": claim_batch_id,
                                "obs_schema": OBS_SCHEMA_VERSION,
                                "batch_size": int(len(events)),
                                "entity_type": batch_entity_type,
                                "op": batch_op,
                                "attempt": int(attempt_max),
                                "result": batch_result,
                                "reason": batch_reason,
                                "mode": "per_event",
                            }
                        )
                    continue

                # Bulk mode: turn the polled rows into one ES _bulk request.
                attempts_by_id = {ev.id: int(ev.attempts or 0) for ev in events}

            remaining = _remaining_grace_seconds()
            if remaining is not None and remaining <= 0.0:
                released = await _release_processing_rows([ev.id for ev in events])
                logger.warning("Shutdown grace exceeded; released %s/%s claimed rows", released, len(events))
                runtime.set_state("STOPPED")
                return

            # Build bulk payload and apply immediate acks (no ES request needed).
            with _start_span(
                "projection.process_batch",
                {
                    "projection": "search",
                    "wordloom.projection": PROJECTION_NAME,
                    "wordloom.worker_id": str(worker_id),
                    "wordloom.claim_batch_id": claim_batch_id,
                    "wordloom.obs_schema": OBS_SCHEMA_VERSION,
                    "batch_size": int(len(events)),
                    "entity_type": batch_entity_type,
                    "op": batch_op,
                    "attempt": int(attempt_max),
                    "mode": "es_bulk_prepare",
                },
                context=batch_parent_ctx,
            ) as bulk_prepare_span:
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
                            "library_id": (str(row.library_id) if getattr(row, "library_id", None) else None),
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
                            processing_started_at=None,
                            next_retry_at=None,
                            error_reason=None,
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
                            processing_started_at=None,
                            attempts=(attempts_by_id.get(ev_id, 0) + 1),
                            next_retry_at=None,
                            error_reason=reason,
                            error=reason,
                            updated_at=now,
                        )
                    )
                    outbox_failed_total.labels(projection=PROJECTION_NAME, op=op, reason=reason).inc()
                    outbox_terminal_failed_total.labels(projection=PROJECTION_NAME, op=op, reason=reason).inc()

                await session.commit()

                if bulk_prepare_span is not None:
                    try:
                        bulk_prepare_span.set_attribute("bulk_ops", int(len(bulk_ops)))
                        bulk_prepare_span.set_attribute(
                            "result",
                            "noop" if (not bulk_ops and not failed_immediately) else "prepared",
                        )
                    except Exception:
                        pass

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
            bulk_span_ref = None
            with _start_span(
                "projection.process_batch",
                {
                    "projection": "search",
                    "wordloom.projection": PROJECTION_NAME,
                    "wordloom.worker_id": str(worker_id),
                    "wordloom.claim_batch_id": claim_batch_id,
                    "wordloom.obs_schema": OBS_SCHEMA_VERSION,
                    "batch_size": int(len(events)),
                    "entity_type": batch_entity_type,
                    "op": batch_op,
                    "attempt": int(attempt_max),
                    "mode": "es_bulk",
                },
                context=batch_parent_ctx,
            ) as batch_span:
                bulk_span_ref = batch_span
                try:
                    remaining = _remaining_grace_seconds()
                    post_coro = client.post(
                        "/_bulk",
                        content=payload.encode("utf-8"),
                        headers={"Content-Type": "application/x-ndjson"},
                    )
                    resp = await post_coro if remaining is None else await asyncio.wait_for(post_coro, timeout=remaining)
                    request_result = "failed" if resp.status_code >= 400 else "success"
                    if batch_span is not None:
                        try:
                            batch_span.set_attribute("result", "ok" if request_result == "success" else "failed")
                        except Exception:
                            pass
                except Exception as exc:  # noqa: BLE001
                    if batch_span is not None:
                        try:
                            batch_span.set_attribute("result", "failed")
                        except Exception:
                            pass

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
                            reason, is_retryable = _classify_attempt_outcome(exc)
                            is_transient = _is_transient_reason(reason)
                            ignore_max_attempts = is_transient and (not terminal_on_transient)
                            should_retry = is_retryable and (ignore_max_attempts or next_attempt < max_attempts)

                            attempts_to_store = min(next_attempt, max_attempts) if ignore_max_attempts else next_attempt
                            delay = _compute_backoff_seconds(
                                attempt=attempts_to_store,
                                base=base_backoff_seconds,
                                max_backoff=max_backoff_seconds,
                            )
                            next_retry_at = now + timedelta(seconds=delay)

                            is_terminal = not should_retry

                            await session.execute(
                                update(SearchOutboxEventModel)
                                .where(
                                    SearchOutboxEventModel.id == ev_id,
                                    SearchOutboxEventModel.owner == worker_id,
                                    SearchOutboxEventModel.status == "processing",
                                    SearchOutboxEventModel.lease_until > now,
                                )
                                .values(
                                    status="pending" if should_retry else "failed",
                                    owner=None,
                                    lease_until=None,
                                    processing_started_at=None,
                                    attempts=attempts_to_store,
                                    next_retry_at=(next_retry_at if should_retry else None),
                                    error_reason=reason,
                                    error=_format_error(exc),
                                    updated_at=now,
                                )
                            )

                            outbox_failed_total.labels(
                                projection=PROJECTION_NAME,
                                op=bulk_outbox_ops[idx],
                                reason=reason,
                            ).inc()

                            if is_terminal:
                                outbox_terminal_failed_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=bulk_outbox_ops[idx],
                                    reason=reason,
                                ).inc()
                            else:
                                outbox_retry_scheduled_total.labels(
                                    projection=PROJECTION_NAME,
                                    op=bulk_outbox_ops[idx],
                                    reason=reason,
                                ).inc()

                        await session.commit()

                    outbox_es_bulk_requests_total.labels(projection=PROJECTION_NAME, result="failed").inc()

                    logger.info(
                        {
                            "event": "projection.process_batch",
                            "layer": "worker",
                            "projection": PROJECTION_NAME,
                            "worker_id": str(worker_id),
                            "claim_batch_id": claim_batch_id,
                            "obs_schema": OBS_SCHEMA_VERSION,
                            "batch_size": int(len(events)),
                            "entity_type": batch_entity_type,
                            "op": batch_op,
                            "attempt": int(attempt_max),
                            "result": "failed",
                            "mode": "es_bulk",
                        }
                    )
                    continue

            outbox_es_bulk_request_duration_seconds.labels(projection=PROJECTION_NAME).observe(
                time.perf_counter() - started
            )

            success_ids: list[Any] = []
            failure_ids: list[Any] = []
            failure_classes: list[str | None] = [None] * len(bulk_event_ids)
            failure_status_codes: list[int | None] = [None] * len(bulk_event_ids)
            failure_error_texts: list[str | None] = [None] * len(bulk_event_ids)

            body: Any
            try:
                body = resp.json() if resp is not None else None
            except Exception:  # noqa: BLE001
                body = None

            if (
                isinstance(body, dict)
                and bool(body.get("items"))
                and fault_es_bulk_partial_enabled
                and isinstance(body.get("items"), list)
                and len(body.get("items") or []) >= 2
            ):
                try:
                    items = body.get("items") or []
                    first = items[0]
                    if isinstance(first, dict):
                        op_key = next(iter(first.keys()), None) or "index"
                        meta = first.get(op_key)
                        meta = dict(meta) if isinstance(meta, dict) else {}
                        meta["status"] = int(fault_es_bulk_partial_status)
                        meta["error"] = {"type": "fault_injection", "reason": "labs_expD_bulk_partial"}
                        items[0] = {op_key: meta}
                        body["items"] = items
                        body["errors"] = True

                        if bulk_span_ref is not None:
                            try:
                                bulk_span_ref.set_attribute("wordloom.labs.es_bulk_partial.injected", True)
                                bulk_span_ref.set_attribute("wordloom.labs.es_bulk_partial.status", int(fault_es_bulk_partial_status))
                            except Exception:
                                pass
                except Exception:
                    pass

            if not isinstance(body, dict) or "items" not in body:
                request_result = "failed"
                for idx, ev_id in enumerate(bulk_event_ids):
                    op = bulk_item_ops[idx]
                    status_int = (resp.status_code if resp is not None else None)
                    failure_status_codes[idx] = status_int
                    failure_classes[idx] = _classify_status_code(status_int)
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
                        failure_status_codes[idx] = None
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
                            failure_status_codes[idx] = status_int
                            failure_classes[idx] = _classify_status_code(status_int)

                            if isinstance(meta, dict):
                                err = meta.get("error")
                                if isinstance(err, dict):
                                    et = err.get("type")
                                    er = err.get("reason")
                                    if et or er:
                                        failure_error_texts[idx] = f"{et}:{er}".strip(":")

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

            if bulk_span_ref is not None:
                try:
                    bulk_span_ref.set_attribute("result", request_result)
                    bulk_span_ref.set_attribute("success_count", int(len(success_ids)))
                    bulk_span_ref.set_attribute("failure_count", int(len(failure_ids)))
                except Exception:
                    pass

            logger.info(
                {
                    "event": "projection.process_batch",
                    "layer": "worker",
                    "projection": PROJECTION_NAME,
                    "worker_id": str(worker_id),
                    "claim_batch_id": claim_batch_id,
                    "obs_schema": OBS_SCHEMA_VERSION,
                    "batch_size": int(len(events)),
                    "entity_type": batch_entity_type,
                    "op": batch_op,
                    "attempt": int(attempt_max),
                    "result": request_result,
                    "mode": "es_bulk",
                }
            )

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
                            processing_started_at=None,
                            next_retry_at=None,
                            error_reason=None,
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

                        status_code = failure_status_codes[idx]
                        reason, is_retryable = _classify_bulk_item_failure(status_code=status_code)

                        is_transient = _is_transient_reason(reason)
                        ignore_max_attempts = is_transient and (not terminal_on_transient)
                        should_retry = (
                            is_retryable
                            and _should_retry_failure_class(failure_class)
                            and (ignore_max_attempts or next_attempt < max_attempts)
                        )
                        next_retry_at = None
                        new_status = "failed"

                        attempts_to_store = min(next_attempt, max_attempts) if ignore_max_attempts else next_attempt

                        if should_retry:
                            delay = _compute_backoff_seconds(
                                attempt=attempts_to_store,
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
                                processing_started_at=None,
                                attempts=attempts_to_store,
                                next_retry_at=next_retry_at,
                                error_reason=reason,
                                error=(failure_error_texts[idx] or f"es_bulk_{failure_class}"),
                                updated_at=now,
                            )
                        )

                        outbox_failed_total.labels(
                            projection=PROJECTION_NAME,
                            op=bulk_outbox_ops[idx],
                            reason=reason,
                        ).inc()

                        if new_status == "pending":
                            outbox_retry_scheduled_total.labels(
                                projection=PROJECTION_NAME,
                                op=bulk_outbox_ops[idx],
                                reason=reason,
                            ).inc()
                        else:
                            outbox_terminal_failed_total.labels(
                                projection=PROJECTION_NAME,
                                op=bulk_outbox_ops[idx],
                                reason=reason,
                            ).inc()

                await session.commit()


def main() -> None:
    asyncio.run(_worker_loop())


if __name__ == "__main__":  # pragma: no cover
    main()
