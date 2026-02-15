#!/usr/bin/env bash
set -euo pipefail

# Usage (via env vars):
#   PORT=30002 DATABASE_URL=... SEARCH_STAGE1_PROVIDER=elastic ELASTIC_URL=... ELASTIC_INDEX=... \
#   PID_FILE=uvicorn_smoke_30002.pid LOG_FILE=server_smoke_30002.log \
#   ./scripts/_smoke_start_uvicorn_wsl.sh

: "${PORT:?PORT is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${SEARCH_STAGE1_PROVIDER:?SEARCH_STAGE1_PROVIDER is required}"
: "${PID_FILE:?PID_FILE is required}"
: "${LOG_FILE:?LOG_FILE is required}"

# Optional for elastic provider
ELASTIC_URL="${ELASTIC_URL:-}"
ELASTIC_INDEX="${ELASTIC_INDEX:-}"

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

# Stop previous smoke instance if pid exists
if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" || true)"
  if [[ -n "${old_pid}" ]]; then
    kill "$old_pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE" || true
fi

# Clear log
rm -f "$LOG_FILE" || true
: > "$LOG_FILE"

# Quick port in use check (best-effort)
if command -v ss >/dev/null 2>&1; then
  if ss -lnt | awk '{print $4}' | grep -Eq ":${PORT}$"; then
    echo "PORT_IN_USE:${PORT}"
    exit 2
  fi
fi

export DATABASE_URL
export SEARCH_STAGE1_PROVIDER
if [[ -n "${ELASTIC_URL}" ]]; then export ELASTIC_URL; fi
if [[ -n "${ELASTIC_INDEX}" ]]; then export ELASTIC_INDEX; fi

nohup python3 -m uvicorn api.app.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_FILE" 2>&1 &
new_pid=$!
echo "$new_pid" > "$PID_FILE"

sleep 0.3
if ! kill -0 "$new_pid" 2>/dev/null; then
  echo "UVICORN_DID_NOT_START"
  tail -n 200 "$LOG_FILE" || true
  exit 1
fi

echo "UVICORN_STARTED:$new_pid"
