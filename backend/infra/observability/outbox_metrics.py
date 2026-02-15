"""Prometheus-style metrics for the search outbox pipeline.

We keep these metrics minimal and low-cardinality:
- produced: emitted when an outbox row is enqueued (same DB transaction as the write)
- processed/failed/lag: emitted by the outbox worker while projecting to Elasticsearch

Expose metrics via:
- API process: /metrics (FastAPI route)
- Worker process: an embedded HTTP server (prometheus_client.start_http_server)
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# ---------------------------------------------------------------------------
# Produced (writer side)
# ---------------------------------------------------------------------------

outbox_produced_total = Counter(
    "outbox_produced_total",
    "Total number of outbox rows successfully enqueued.",
    ["event_type", "entity_type"],
)

# ---------------------------------------------------------------------------
# Worker-side metrics (projection)
# ---------------------------------------------------------------------------

outbox_processed_total = Counter(
    "outbox_processed_total",
    "Total number of outbox rows successfully processed by the projection worker.",
    ["projection", "op"],
)

outbox_failed_total = Counter(
    "outbox_failed_total",
    "Total number of outbox rows that failed processing in the projection worker.",
    ["projection", "op", "reason"],
)

outbox_retry_scheduled_total = Counter(
    "outbox_retry_scheduled_total",
    "Total number of outbox rows that were scheduled for retry (pending + next_retry_at set).",
    ["projection", "op", "reason"],
)

outbox_idempotent_noop_total = Counter(
    "outbox_idempotent_noop_total",
    "Total number of outbox operations that were a safe no-op (idempotent), e.g. delete on a missing doc.",
    ["projection", "op", "reason"],
)

outbox_terminal_failed_total = Counter(
    "outbox_terminal_failed_total",
    "Total number of outbox rows that transitioned into terminal failed state.",
    ["projection", "op", "reason"],
)

outbox_lag_events = Gauge(
    "outbox_lag_events",
    "Current number of unprocessed outbox rows.",
    ["projection"],
)

outbox_oldest_age_seconds = Gauge(
    "outbox_oldest_age_seconds",
    "Age of the oldest unprocessed outbox row (seconds).",
    ["projection"],
)

outbox_inflight_events = Gauge(
    "outbox_inflight_events",
    "Current number of outbox rows in processing state (leased by some worker).",
    ["projection"],
)

outbox_stuck_processing_events = Gauge(
    "outbox_stuck_processing_events",
    "Current number of outbox rows in processing state that appear stuck (expired lease or exceeded max processing time).",
    ["projection"],
)

outbox_last_success_timestamp_seconds = Gauge(
    "outbox_last_success_timestamp_seconds",
    "Unix timestamp (seconds) of the last successfully processed outbox row.",
    ["projection"],
)


# ---------------------------------------------------------------------------
# Rebuild bookkeeping (operational)
# ---------------------------------------------------------------------------

projection_rebuild_duration_seconds = Gauge(
    "projection_rebuild_duration_seconds",
    "Duration of the last rebuild run (seconds).",
    ["projection"],
)

projection_rebuild_last_finished_timestamp_seconds = Gauge(
    "projection_rebuild_last_finished_timestamp_seconds",
    "Unix timestamp (seconds) when the last rebuild finished.",
    ["projection"],
)

projection_rebuild_last_success = Gauge(
    "projection_rebuild_last_success",
    "Whether the last rebuild run succeeded (1) or failed (0).",
    ["projection"],
)

# ---------------------------------------------------------------------------
# Elasticsearch bulk metrics (worker side)
# ---------------------------------------------------------------------------

outbox_es_bulk_requests_total = Counter(
    "outbox_es_bulk_requests_total",
    "Total number of Elasticsearch bulk requests made by the outbox worker.",
    ["projection", "result"],  # result: success | partial | failed
)

outbox_es_bulk_items_total = Counter(
    "outbox_es_bulk_items_total",
    "Total number of outbox items attempted via Elasticsearch bulk requests.",
    ["projection", "op", "result"],  # result: success | failed
)

outbox_es_bulk_item_failures_total = Counter(
    "outbox_es_bulk_item_failures_total",
    "Total number of failed Elasticsearch bulk items, bucketed by coarse failure class.",
    ["projection", "op", "failure_class"],
)

outbox_es_bulk_request_duration_seconds = Histogram(
    "outbox_es_bulk_request_duration_seconds",
    "Duration of Elasticsearch bulk requests (seconds).",
    ["projection"],
    buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0),
)


__all__ = [
    "outbox_produced_total",
    "outbox_processed_total",
    "outbox_idempotent_noop_total",
    "outbox_failed_total",
    "outbox_retry_scheduled_total",
    "outbox_terminal_failed_total",
    "outbox_lag_events",
    "outbox_oldest_age_seconds",
    "outbox_inflight_events",
    "outbox_stuck_processing_events",
    "outbox_last_success_timestamp_seconds",
    "projection_rebuild_duration_seconds",
    "projection_rebuild_last_finished_timestamp_seconds",
    "projection_rebuild_last_success",
    "outbox_es_bulk_requests_total",
    "outbox_es_bulk_items_total",
    "outbox_es_bulk_item_failures_total",
    "outbox_es_bulk_request_duration_seconds",
]
