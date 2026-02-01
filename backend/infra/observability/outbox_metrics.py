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

outbox_lag_events = Gauge(
    "outbox_lag_events",
    "Current number of unprocessed outbox rows.",
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
    "outbox_failed_total",
    "outbox_lag_events",
    "outbox_es_bulk_requests_total",
    "outbox_es_bulk_items_total",
    "outbox_es_bulk_item_failures_total",
    "outbox_es_bulk_request_duration_seconds",
]
