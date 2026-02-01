#!/usr/bin/env bash
set -euo pipefail

# Run API with env file (.env.dev/.env.test).
# Usage:
#   ./backend/scripts/run_api.sh ../.env.dev

ENV_FILE="${1:-../.env.dev}"

# Resolve repo root relative to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

if [[ "$ENV_FILE" != /* ]]; then
  ENV_FILE="$REPO_ROOT/$ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[run_api] env file not found: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

PORT="${API_PORT:-30001}"

cd "$BACKEND_DIR"
exec uvicorn api.app.main:app --host 0.0.0.0 --port "$PORT" --reload
