#!/usr/bin/env bash
set -euo pipefail

# Run outbox worker with env file (.env.dev/.env.test).
# Usage:
#   ./backend/scripts/run_worker.sh ../.env.dev

ENV_FILE="${1:-../.env.dev}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

if [[ "$ENV_FILE" != /* ]]; then
  ENV_FILE="$REPO_ROOT/$ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[run_worker] env file not found: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

cd "$BACKEND_DIR"
exec python3 scripts/search_outbox_worker.py
