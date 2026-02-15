#!/usr/bin/env bash
set -euo pipefail

# Labs-005 Experiment 6 (v4): Chronicle worker runtime hardening validation.
# Assumes DB is running and env vars are set:
#   DATABASE_URL
# Optional:
#   WORDLOOM_ENV, OUTBOX_WORKER_ID

METRICS_PORT="${OUTBOX_METRICS_PORT:-9110}"
HTTP_PORT="${OUTBOX_HTTP_PORT:-$((METRICS_PORT + 2))}"
GRACE_SECONDS="${OUTBOX_SHUTDOWN_GRACE_SECONDS:-10}"

export OUTBOX_METRICS_PORT="$METRICS_PORT"
export OUTBOX_HTTP_PORT="$HTTP_PORT"
export OUTBOX_SHUTDOWN_GRACE_SECONDS="$GRACE_SECONDS"

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  fi
fi

echo "[labs-005/e6] Starting chronicle_outbox_worker (metrics=:$METRICS_PORT http=:$HTTP_PORT grace=${GRACE_SECONDS}s)"

"$PYTHON_BIN" backend/scripts/chronicle_outbox_worker.py &
PID=$!

cleanup() {
  if kill -0 "$PID" 2>/dev/null; then
    echo "[labs-005/e6] cleanup: killing worker PID=$PID"
    kill -KILL "$PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

sleep 1

echo "[labs-005/e6] GET /healthz"
curl -fsS "http://localhost:${HTTP_PORT}/healthz" | cat
echo

echo "[labs-005/e6] GET /readyz"
curl -fsS "http://localhost:${HTTP_PORT}/readyz" | cat
echo

# Optional guardrail exercise: if docker is available inside WSL, briefly stop the
# devtest DB container to observe /readyz flipping to 503, then restore.
if command -v docker >/dev/null 2>&1; then
  echo "[labs-005/e6] Attempting guardrail exercise by stopping DB briefly (best-effort)"
  DB_CID="$(docker ps --format '{{.ID}} {{.Ports}}' | awk '/0\.0\.0\.0:5435->5432\/tcp|\[::\]:5435->5432\/tcp/{print $1; exit}')"
  if [ -n "$DB_CID" ]; then
    echo "[labs-005/e6] Stopping DB container id=$DB_CID"
    docker stop -t 1 "$DB_CID" >/dev/null || true
    sleep 2
    echo "[labs-005/e6] GET /readyz (expected 503 while DB down)"
    curl -fsS "http://localhost:${HTTP_PORT}/readyz" | cat || true
    echo
    echo "[labs-005/e6] Restarting DB container id=$DB_CID"
    docker start "$DB_CID" >/dev/null || true
    sleep 2
    echo "[labs-005/e6] GET /readyz (expected 200 after DB restored)"
    curl -fsS "http://localhost:${HTTP_PORT}/readyz" | cat || true
    echo
  else
    echo "[labs-005/e6] No DB container exposing :5435 found; skipping guardrail exercise"
  fi
else
  echo "[labs-005/e6] docker not available; skipping guardrail exercise"
fi

echo "[labs-005/e6] Sending SIGTERM"
kill -TERM "$PID"

START=$(date +%s)
TIMEOUT=$((GRACE_SECONDS + 5))
while kill -0 "$PID" 2>/dev/null; do
  NOW=$(date +%s)
  ELAPSED=$((NOW - START))
  if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
    echo "[labs-005/e6] FAIL: worker did not exit within ${TIMEOUT}s" >&2
    exit 1
  fi
  sleep 0.2
done

echo "[labs-005/e6] OK: worker exited"
trap - EXIT
