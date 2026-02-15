#!/usr/bin/env bash
set -euo pipefail

# Labs-004 Experiment 6 (v4): daemon runtime hardening validation.
# Assumes DB + ES are already running and env vars are set:
#   DATABASE_URL, ELASTIC_URL, ELASTIC_INDEX
# Optional:
#   WORDLOOM_ENV, OUTBOX_WORKER_ID

METRICS_PORT="${OUTBOX_METRICS_PORT:-9109}"
HTTP_PORT="${OUTBOX_HTTP_PORT:-$((METRICS_PORT + 2))}"
GRACE_SECONDS="${OUTBOX_SHUTDOWN_GRACE_SECONDS:-10}"

export OUTBOX_METRICS_PORT="$METRICS_PORT"
export OUTBOX_HTTP_PORT="$HTTP_PORT"
export OUTBOX_SHUTDOWN_GRACE_SECONDS="$GRACE_SECONDS"
export OUTBOX_REQUIRE_ES_READY="${OUTBOX_REQUIRE_ES_READY:-1}"

echo "[labs-004/v4] Starting search_outbox_worker (metrics=:$METRICS_PORT http=:$HTTP_PORT grace=${GRACE_SECONDS}s)"

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  fi
fi

"$PYTHON_BIN" backend/scripts/search_outbox_worker.py &
PID=$!

cleanup() {
  if kill -0 "$PID" 2>/dev/null; then
    echo "[labs-004/v4] cleanup: killing worker PID=$PID"
    kill -KILL "$PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

sleep 1

echo "[labs-004/v4] GET /healthz"
curl -fsS "http://localhost:${HTTP_PORT}/healthz" | cat
echo

echo "[labs-004/v4] GET /readyz (may be 503 if deps not ready)"
curl -fsS "http://localhost:${HTTP_PORT}/readyz" | cat || true
echo

echo "[labs-004/v4] Sending SIGTERM"
kill -TERM "$PID"

START=$(date +%s)
TIMEOUT=$((GRACE_SECONDS + 5))
while kill -0 "$PID" 2>/dev/null; do
  NOW=$(date +%s)
  ELAPSED=$((NOW - START))
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "[labs-004/v4] FAIL: worker did not exit within ${TIMEOUT}s" >&2
    exit 1
  fi
  sleep 0.2
done

echo "[labs-004/v4] OK: worker exited"
trap - EXIT
