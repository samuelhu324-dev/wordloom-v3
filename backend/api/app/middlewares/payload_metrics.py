from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from api.app.shared.request_context import RequestContext, set_request_context, reset_request_context


logger = logging.getLogger(__name__)


class PayloadMetricsMiddleware(BaseHTTPMiddleware):
    """HTTP-level metrics middleware.

    Emits a structured log for every request/response:
    - correlation_id (X-Request-Id)
    - duration_ms
    - response_bytes (best-effort)

    Also ensures correlation_id is available as request.state.correlation_id and
    is returned to clients via response header X-Request-Id.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        # Prefer explicit request id, otherwise allow resource requests (e.g. <img>)
        # to correlate via query param `cid`.
        correlation_id = (
            request.headers.get("X-Request-Id")
            or request.query_params.get("cid")
            or str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        # Best-effort: attach correlation_id onto the active request span so
        # operators can pivot correlation_id -> trace in Jaeger.
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span is not None:
                span.set_attribute("correlation_id", correlation_id)
                span.set_attribute("wordloom.correlation_id", correlation_id)
        except Exception:
            # Never break request handling.
            pass

        token = set_request_context(
            RequestContext(
                correlation_id=correlation_id,
                route=request.url.path,
                method=request.method,
            )
        )

        # Entry log: proves request hit the application and pins correlation_id.
        logger.info(
            {
                "event": "http.request_received",
                "layer": "middleware",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "cid": request.query_params.get("cid"),
                "cache_bust": request.query_params.get("cache_bust"),
            }
        )

        try:
            response: Response = await call_next(request)
        finally:
            # Prevent context leakage across concurrent requests.
            reset_request_context(token)

        # Handlers may override request.state.correlation_id (e.g. when `cid` is
        # computed from query params). Use the final value for logging/headers.
        final_correlation_id = getattr(request.state, "correlation_id", None) or correlation_id

        duration_ms = (time.perf_counter() - start) * 1000

        response_bytes: Optional[int] = None
        cl = response.headers.get("content-length")
        if cl and cl.isdigit():
            response_bytes = int(cl)
        else:
            body = getattr(response, "body", None)
            if isinstance(body, (bytes, bytearray)):
                response_bytes = len(body)

        logger.info(
            {
                "event": "http.response",
                "layer": "middleware",
                "correlation_id": final_correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_bytes": response_bytes,
            }
        )

        response.headers.setdefault("X-Request-Id", final_correlation_id)
        return response
