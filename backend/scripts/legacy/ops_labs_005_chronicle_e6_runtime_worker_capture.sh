#!/usr/bin/env bash
set -euo pipefail

# Capture wrapper for Labs-005 Experiment 6 (v4 runtime):
# Runs the experiment and writes a snapshot under docs/architecture/runbook/labs/_snapshots.

REPO_ROOT_DIR=${REPO_ROOT_DIR:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
cd "$REPO_ROOT_DIR"

SNAP_DIR="docs/architecture/runbook/labs/_snapshots"
mkdir -p "$SNAP_DIR"
TS="$(date +%Y%m%dT%H%M%S)"
SNAP="$SNAP_DIR/labs-005-chronicle-e6-runtime-$TS.txt"

{
  echo "# labs-005 experiment 6 (v4) chronicle worker runtime"
  echo "# started_at=$(date -Is)"
  echo "# DATABASE_URL=${DATABASE_URL:-}"
  echo "# OUTBOX_WORKER_ID=${OUTBOX_WORKER_ID:-} OUTBOX_METRICS_PORT=${OUTBOX_METRICS_PORT:-} OUTBOX_HTTP_PORT=${OUTBOX_HTTP_PORT:-}"
  echo "# OUTBOX_SHUTDOWN_GRACE_SECONDS=${OUTBOX_SHUTDOWN_GRACE_SECONDS:-} OUTBOX_DB_PING_FAILS_BEFORE_DRAINING=${OUTBOX_DB_PING_FAILS_BEFORE_DRAINING:-}"
  echo
  echo "## Phase A: normal deps (health/ready 200 + SIGTERM exit)"
  echo
  bash backend/scripts/ops_labs_005_chronicle_e6_runtime_worker.sh
  echo

  echo "## Phase B: guardrails (unreachable DB => readyz=503 + stop claiming)"
  echo "# Note: this phase uses a deliberately bad DATABASE_URL to force db ping failures."
  echo

  BAD_METRICS_PORT="${OUTBOX_METRICS_PORT_BAD:-9120}"
  BAD_HTTP_PORT="${OUTBOX_HTTP_PORT_BAD:-9122}"
  BAD_GRACE_SECONDS="${OUTBOX_SHUTDOWN_GRACE_SECONDS_BAD:-10}"

  export OUTBOX_WORKER_ID="${OUTBOX_WORKER_ID_BAD:-c-v4-bad-db}"
  export OUTBOX_METRICS_PORT="$BAD_METRICS_PORT"
  export OUTBOX_HTTP_PORT="$BAD_HTTP_PORT"
  export OUTBOX_SHUTDOWN_GRACE_SECONDS="$BAD_GRACE_SECONDS"
  export OUTBOX_DB_PING_INTERVAL_SECONDS="${OUTBOX_DB_PING_INTERVAL_SECONDS_BAD:-0.2}"
  export OUTBOX_DB_PING_TIMEOUT_SECONDS="${OUTBOX_DB_PING_TIMEOUT_SECONDS_BAD:-0.2}"
  export OUTBOX_DB_PING_FAILS_BEFORE_DRAINING="${OUTBOX_DB_PING_FAILS_BEFORE_DRAINING_BAD:-1}"
  export OUTBOX_POLL_INTERVAL_SECONDS="${OUTBOX_POLL_INTERVAL_SECONDS_BAD:-0.2}"

  PYTHON_BIN="${PYTHON_BIN:-python}"
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    if command -v python3 >/dev/null 2>&1; then
      PYTHON_BIN=python3
    fi
  fi

  BAD_DB_URL="${DATABASE_URL_BAD:-postgresql+psycopg://wordloom:wordloom@localhost:5999/wordloom_test}"
  echo "[phase-b] starting chronicle_outbox_worker with bad DATABASE_URL=$BAD_DB_URL"

  DATABASE_URL="$BAD_DB_URL" "$PYTHON_BIN" backend/scripts/chronicle_outbox_worker.py &
  PID=$!

  kill_if_running() {
    if kill -0 "$PID" 2>/dev/null; then
      kill -KILL "$PID" 2>/dev/null || true
    fi
  }
  trap kill_if_running RETURN

  sleep 1
  echo "[phase-b] GET /healthz (expect 200 if loop alive)"
  curl -fsS "http://localhost:${BAD_HTTP_PORT}/healthz" | cat || true
  echo

  echo "[phase-b] Waiting for /readyz to flip to 503 (db_unhealthy) ..."
  deadline=$(( $(date +%s) + 10 ))
  while true; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${BAD_HTTP_PORT}/readyz" || true)
    if [ "$code" = "503" ]; then
      echo "[phase-b] OK: /readyz returned 503"
      break
    fi
    if [ $(date +%s) -ge $deadline ]; then
      echo "[phase-b] FAIL: /readyz did not return 503 within 10s (last_http_code=$code)" >&2
      break
    fi
    sleep 0.2
  done

  echo "[phase-b] Sending SIGTERM"
  kill -TERM "$PID" || true

  start=$(date +%s)
  timeout=$((BAD_GRACE_SECONDS + 5))
  while kill -0 "$PID" 2>/dev/null; do
    now=$(date +%s)
    elapsed=$((now - start))
    if [ "$elapsed" -ge "$timeout" ]; then
      echo "[phase-b] FAIL: worker did not exit within ${timeout}s" >&2
      break
    fi
    sleep 0.2
  done
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "[phase-b] OK: worker exited"
  fi

  trap - RETURN
  echo
  echo "SNAPSHOT=$SNAP"
} 2>&1 | tee "$SNAP"
