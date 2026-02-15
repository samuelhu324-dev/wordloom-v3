"""Tracing utilities (OpenTelemetry).

Design goals:
- Opt-in by default: no tracing unless explicitly enabled.
- Minimal, safe defaults that work for local labs and can be promoted to prod.
- Provide helpers for async boundary propagation via W3C trace context.

Environment knobs (supported by this module):
- WORDLOOM_TRACING_ENABLED: "1"/"true" to enable tracing. Default: disabled.
- OTEL_SDK_DISABLED: standard OTel switch; if true, disables tracing.
- OTEL_SERVICE_NAME: optional; otherwise callers pass a default.
- OTEL_EXPORTER_OTLP_ENDPOINT: base endpoint (e.g., http://localhost:4318).
- OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: optional full traces endpoint.
- OTEL_TRACES_SAMPLER: "always_on" | "always_off" | "traceidratio".
- OTEL_TRACES_SAMPLER_ARG: for traceidratio (0..1).

Notes:
- We intentionally keep this module dependency-local to `infra` so scripts and API
  can share the same tracing bootstrap.
"""

from __future__ import annotations

import logging
import os
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse


def _truthy(raw: Optional[str]) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def is_tracing_enabled() -> bool:
    # Standard OTel switch: OTEL_SDK_DISABLED=true means disabled.
    if _truthy(os.getenv("OTEL_SDK_DISABLED")):
        return False
    return _truthy(os.getenv("WORDLOOM_TRACING_ENABLED"))


def _build_otlp_http_traces_endpoint() -> Optional[str]:
    # Prefer standard traces-specific endpoint.
    traces_endpoint = (os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or "").strip()
    if traces_endpoint:
        return traces_endpoint

    # Otherwise use the base endpoint and append /v1/traces.
    base = (os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip()
    if not base:
        return None

    base = base.rstrip("/")
    if base.endswith("/v1/traces"):
        return base
    return f"{base}/v1/traces"


def _normalize_base_endpoint(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    # OTel envs sometimes provide host:port without scheme.
    if "://" not in raw:
        return f"http://{raw}"
    return raw


def _infer_otlp_protocol(*, base_endpoint: str, traces_endpoint: str) -> str:
    """Return normalized protocol: 'grpc' or 'http/protobuf'."""

    explicit = (os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL") or "").strip().lower()
    if explicit in {"grpc"}:
        return "grpc"
    if explicit in {"http/protobuf", "http" , "http/proto", "http_protobuf"}:
        return "http/protobuf"

    # If traces endpoint is explicitly set and looks like HTTP OTLP.
    if traces_endpoint:
        if "/v1/traces" in traces_endpoint:
            return "http/protobuf"
        # No path: could still be base, fall through.

    normalized = _normalize_base_endpoint(base_endpoint)
    if normalized:
        parsed = urlparse(normalized)
        if parsed.port == 4317:
            return "grpc"
        if parsed.port == 4318:
            return "http/protobuf"

    # Default to HTTP/protobuf because it works with Jaeger all-in-one and is
    # easiest to test locally via plain HTTP.
    return "http/protobuf"


def _resolve_otlp_export_target() -> tuple[Optional[str], str]:
    """Return (target, protocol).

    - For grpc: target is base endpoint (no /v1/traces).
    - For http/protobuf: target is full traces endpoint (includes /v1/traces).

    Returns (None, protocol) when exporter is intentionally not configured.
    """

    traces_endpoint = (os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or "").strip()
    base_endpoint = (os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip()
    protocol = _infer_otlp_protocol(base_endpoint=base_endpoint, traces_endpoint=traces_endpoint)

    if protocol == "grpc":
        raw = traces_endpoint or base_endpoint
        if not raw:
            return None, protocol
        return _normalize_base_endpoint(raw).rstrip("/"), protocol

    # http/protobuf
    http_target = _build_otlp_http_traces_endpoint()
    return http_target, protocol


def setup_tracing(*, default_service_name: str) -> bool:
    """Initialize OpenTelemetry tracing if enabled.

    Safe to call multiple times. Returns whether tracing is enabled.
    """

    logger = logging.getLogger(__name__)

    if not is_tracing_enabled():
        logger.info(
            {
                "event": "tracing.startup",
                "enabled": False,
                "reason": "disabled",
                "WORDLOOM_TRACING_ENABLED": (os.getenv("WORDLOOM_TRACING_ENABLED") or "").strip(),
                "OTEL_SDK_DISABLED": (os.getenv("OTEL_SDK_DISABLED") or "").strip(),
            }
        )
        return False

    # Import lazily so importing this module doesn't require OTel unless enabled.
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_OFF,
        ALWAYS_ON,
        TraceIdRatioBased,
    )

    # Avoid re-initializing if already set (important for tests and reloads).
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        return True

    service_name = (os.getenv("OTEL_SERVICE_NAME") or "").strip() or default_service_name

    sampler_name = (os.getenv("OTEL_TRACES_SAMPLER") or "").strip().lower() or "traceidratio"
    sampler_arg = (os.getenv("OTEL_TRACES_SAMPLER_ARG") or "").strip()

    if sampler_name in {"always_on", "on"}:
        sampler = ALWAYS_ON
    elif sampler_name in {"always_off", "off"}:
        sampler = ALWAYS_OFF
    else:
        # Default: traceidratio
        ratio = 0.05
        if sampler_arg:
            try:
                ratio = float(sampler_arg)
            except ValueError:
                ratio = 0.05
        ratio = max(0.0, min(1.0, ratio))
        sampler = TraceIdRatioBased(ratio)

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource, sampler=sampler)

    otlp_target_raw, protocol = _resolve_otlp_export_target()
    otlp_target = otlp_target_raw

    exporter_reason = "not_configured"
    collector_reachable: Optional[bool] = None

    if not otlp_target:
        exporter_reason = "no_otlp_target"

    if otlp_target:
        # If the collector isn't running, the default OTLP exporters will emit
        # noisy stack traces on every export attempt. Make local dev/test safe:
        # do a quick reachability probe and skip exporter if unreachable.
        host, port = _try_parse_host_port(otlp_target)
        if host and port:
            collector_reachable = _tcp_connectable(host, port, timeout_s=0.25)
        if host and port and not collector_reachable:
            logger.warning(
                {
                    "event": "tracing.exporter_unreachable",
                    "enabled": True,
                    "otlp_protocol": protocol,
                    "otlp_target": otlp_target,
                    "hint": "Start Jaeger/OTel Collector or unset WORDLOOM_TRACING_ENABLED.",
                }
            )
            exporter_reason = "collector_unreachable"
            otlp_target = None

    exporter_configured = False
    if otlp_target:
        if protocol == "grpc":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=otlp_target)
        else:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=otlp_target)

        provider.add_span_processor(BatchSpanProcessor(_SafeSpanExporter(exporter)))
        exporter_configured = True
        exporter_reason = "configured"

    logger.info(
        {
            "event": "tracing.startup",
            "enabled": True,
            "otel_service_name": service_name,
            "otlp_protocol": protocol,
            "otlp_target": otlp_target or "",
            "otlp_target_raw": otlp_target_raw or "",
            "collector_reachable": collector_reachable,
            "exporter_configured": exporter_configured,
            "exporter_reason": exporter_reason,
            "sampler": sampler_name,
            "sampler_arg": sampler_arg,
        }
    )

    logger.info(
        {
            "event": "tracing.config",
            "enabled": True,
            "otel_service_name": service_name,
            "otlp_protocol": protocol,
            "otlp_target": otlp_target or "",
            "sampler": sampler_name,
            "sampler_arg": sampler_arg,
        }
    )

    trace.set_tracer_provider(provider)
    return True


def _try_parse_host_port(endpoint: str) -> tuple[Optional[str], Optional[int]]:
    raw = (endpoint or "").strip()
    if not raw:
        return None, None

    # Accept host:port by normalizing to http://host:port.
    if "://" not in raw:
        raw = f"http://{raw}"

    parsed = urlparse(raw)
    host = parsed.hostname
    port = parsed.port
    if not host:
        return None, None
    if port is None:
        if parsed.scheme == "https":
            port = 443
        else:
            port = 80
    return host, port


def _tcp_connectable(host: str, port: int, *, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


class _SafeSpanExporter:
    """Wrap an OTel SpanExporter and never raise from export().

    The default OTLP exporters may raise on connection errors; the SDK logs a
    full stack trace which is too noisy for local dev/test.
    """

    def __init__(self, inner):
        self._inner = inner

    def export(self, spans):
        from opentelemetry.sdk.trace.export import SpanExportResult

        try:
            return self._inner.export(spans)
        except Exception:
            return SpanExportResult.FAILURE

    def shutdown(self):
        try:
            return self._inner.shutdown()
        except Exception:
            return None

    def force_flush(self, timeout_millis: int = 30000):
        try:
            return self._inner.force_flush(timeout_millis=timeout_millis)
        except Exception:
            return False


def instrument_fastapi(app) -> None:
    """Instrument a FastAPI app (inbound HTTP spans)."""

    if not is_tracing_enabled():
        return

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app)


def instrument_httpx() -> None:
    """Instrument httpx globally (outbound HTTP spans)."""

    if not is_tracing_enabled():
        return

    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor().instrument()


def instrument_sqlalchemy_engine(engine) -> None:
    """Instrument SQLAlchemy engine.

    For AsyncEngine, pass `engine.sync_engine`.
    """

    if not is_tracing_enabled():
        return

    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine)


def inject_trace_context() -> Tuple[Optional[str], Optional[str]]:
    """Return (traceparent, tracestate) for the current context."""

    if not is_tracing_enabled():
        return None, None

    from opentelemetry.propagate import inject

    carrier: dict[str, str] = {}
    inject(carrier)
    return carrier.get("traceparent"), carrier.get("tracestate")


def extract_context(*, traceparent: Optional[str], tracestate: Optional[str]):
    """Extract an OTel context from W3C headers (best-effort)."""

    if not is_tracing_enabled() or not traceparent:
        return None

    from opentelemetry.propagate import extract

    carrier: dict[str, str] = {"traceparent": traceparent}
    if tracestate:
        carrier["tracestate"] = tracestate
    return extract(carrier)
