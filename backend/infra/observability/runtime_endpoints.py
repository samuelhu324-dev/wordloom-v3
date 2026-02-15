from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


@dataclass
class RuntimeSnapshot:
    projection: str
    worker_id: str
    state: str
    stop_requested: bool
    stop_reason: str | None
    last_loop_at_mono: float
    last_db_ok: bool
    last_db_error: str | None
    consecutive_db_failures: int


class RuntimeState:
    def __init__(self, *, projection: str, worker_id: str) -> None:
        self._lock = threading.Lock()
        self._projection = projection
        self._worker_id = worker_id

        now = time.monotonic()
        self._state = "RUNNING"  # RUNNING | DEGRADED | DRAINING | STOPPED
        self._stop_requested = False
        self._stop_reason: str | None = None

        self._last_loop_at_mono = now
        self._last_db_ok = True
        self._last_db_error: str | None = None
        self._consecutive_db_failures = 0

    def mark_loop_tick(self) -> None:
        with self._lock:
            self._last_loop_at_mono = time.monotonic()

    def request_stop(self, reason: str) -> None:
        with self._lock:
            if self._stop_requested:
                return
            self._stop_requested = True
            self._stop_reason = reason
            if self._state != "STOPPED":
                self._state = "DRAINING"

    def set_state(self, state: str) -> None:
        with self._lock:
            self._state = state

    def set_db_check(self, *, ok: bool, error: str | None = None) -> None:
        with self._lock:
            self._last_db_ok = bool(ok)
            self._last_db_error = error
            if ok:
                self._consecutive_db_failures = 0
            else:
                self._consecutive_db_failures += 1

    def snapshot(self) -> RuntimeSnapshot:
        with self._lock:
            return RuntimeSnapshot(
                projection=self._projection,
                worker_id=self._worker_id,
                state=self._state,
                stop_requested=self._stop_requested,
                stop_reason=self._stop_reason,
                last_loop_at_mono=self._last_loop_at_mono,
                last_db_ok=self._last_db_ok,
                last_db_error=self._last_db_error,
                consecutive_db_failures=self._consecutive_db_failures,
            )


def start_runtime_http_server(
    *,
    port: int,
    state: RuntimeState,
    health_max_silence_seconds: float = 10.0,
    extra_ready_predicate: Callable[[], tuple[bool, str | None]] | None = None,
) -> ThreadingHTTPServer:
    """Start a tiny HTTP server for /healthz and /readyz.

    This intentionally avoids extra dependencies (aiohttp/fastapi) so workers can
    stay as simple scripts.
    """

    def _is_healthy() -> tuple[bool, str | None, RuntimeSnapshot]:
        snap = state.snapshot()
        age = time.monotonic() - snap.last_loop_at_mono
        if snap.state == "STOPPED":
            return False, "stopped", snap
        if age > health_max_silence_seconds:
            return False, f"loop_silence>{health_max_silence_seconds}s", snap
        return True, None, snap

    def _is_ready() -> tuple[bool, str | None, RuntimeSnapshot]:
        snap = state.snapshot()
        if snap.stop_requested or snap.state in {"DRAINING", "STOPPED"}:
            return False, "draining", snap
        if not snap.last_db_ok:
            return False, "db_unhealthy", snap
        if extra_ready_predicate is not None:
            ok, reason = extra_ready_predicate()
            if not ok:
                return False, reason or "dependency_unhealthy", snap
        return True, None, snap

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in {"/healthz", "/readyz"}:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"not_found"}')
                return

            if self.path == "/healthz":
                ok, reason, snap = _is_healthy()
            else:
                ok, reason, snap = _is_ready()

            body = {
                "ok": ok,
                "reason": reason,
                "projection": snap.projection,
                "worker_id": snap.worker_id,
                "state": snap.state,
                "stop_requested": snap.stop_requested,
                "stop_reason": snap.stop_reason,
                "last_loop_ago_seconds": max(0.0, time.monotonic() - snap.last_loop_at_mono),
                "db": {
                    "ok": snap.last_db_ok,
                    "consecutive_failures": snap.consecutive_db_failures,
                    "last_error": snap.last_db_error,
                },
            }

            status = HTTPStatus.OK if ok else HTTPStatus.SERVICE_UNAVAILABLE
            payload = json.dumps(body, separators=(",", ":")).encode("utf-8")

            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            # Keep runtime endpoints quiet; workers already log plenty.
            return

    httpd = ThreadingHTTPServer(("0.0.0.0", int(port)), Handler)
    thread = threading.Thread(target=httpd.serve_forever, name=f"runtime-http:{port}", daemon=True)
    thread.start()
    return httpd
