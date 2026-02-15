"""
Logging configuration

Provides:
- setup_logging: Configure logging at application startup
- get_logger: Get logger instance
"""

import logging
import json
from datetime import datetime, timezone
import os
from .setting import get_settings


_STANDARD_LOG_RECORD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class JsonLineFormatter(logging.Formatter):
    """Format LogRecord into one-line JSON.

    Notes:
    - If the log message is a dict (common in structured logging), merge it into the JSON.
    - Include any `extra={...}` fields as top-level JSON keys.
    - Keep output as a single line (JSONL), suitable for grep/jq/ELK/Loki.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        # Merge dict-style structured logs: logger.info({"event": ...})
        if isinstance(record.msg, dict):
            for k, v in record.msg.items():
                payload[k] = _json_safe(v)
            # Provide a default message field for consistency.
            payload.setdefault("message", payload.get("event") or "")
        else:
            payload["message"] = record.getMessage()

        # Merge any extra fields.
        for k, v in record.__dict__.items():
            if k in _STANDARD_LOG_RECORD_ATTRS:
                continue
            # Avoid overriding explicit keys from dict payload unless extra is intended.
            if k not in payload:
                payload[k] = _json_safe(v)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def _truthy(raw: str | None) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_tracing_enabled() -> bool:
    # Keep this local to avoid importing infra in the API config layer.
    if _truthy(os.getenv("OTEL_SDK_DISABLED")):
        return False
    return _truthy(os.getenv("WORDLOOM_TRACING_ENABLED"))


class _TraceContextFilter(logging.Filter):
    """Best-effort inject trace/span ids into log records.

    When tracing is disabled, this filter is effectively a no-op.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if not _is_tracing_enabled():
            return True

        # Avoid overriding explicit fields.
        if hasattr(record, "trace_id") and hasattr(record, "span_id"):
            return True

        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            ctx = span.get_span_context() if span is not None else None
            if ctx is not None and getattr(ctx, "is_valid", False):
                if not hasattr(record, "trace_id"):
                    record.trace_id = f"{ctx.trace_id:032x}"
                if not hasattr(record, "span_id"):
                    record.span_id = f"{ctx.span_id:016x}"
        except Exception:
            # Never break logging.
            return True

        return True


def _json_safe(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def setup_logging():
    """
    Configure application logging

    Features:
    - Configurable log level from settings
    - Standard Python logging format
    - JSON output ready for production

    Should be called at application startup (main.py)
    """
    settings = get_settings()

    level = getattr(logging, settings.log_level, logging.INFO)

    if getattr(settings, "log_json", True):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(JsonLineFormatter())
        handler.addFilter(_TraceContextFilter())

        root = logging.getLogger()
        root.setLevel(level)
        for h in list(root.handlers):
            root.removeHandler(h)
        root.addHandler(handler)

        # Ensure uvicorn loggers also emit JSON lines (they are configured before app import).
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            l = logging.getLogger(name)
            l.setLevel(level)
            for h in list(l.handlers):
                l.removeHandler(h)
            l.addHandler(handler)
            l.propagate = False
    else:
        # Fallback to standard plain-text formatting
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=level,
            format=log_format,
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance by name

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)
