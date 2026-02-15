#!/usr/bin/env bash
set -euo pipefail

# Run API with env file (.env.dev/.env.test).
# Usage:
#   ./backend/scripts/ops/run_api.sh ../.env.dev

ENV_FILE="${1:-../.env.dev}"

# Resolve repo root relative to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
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

RUN_PREFIX=()
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  :
elif [[ -f "$BACKEND_DIR/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$BACKEND_DIR/.venv/bin/activate"
elif [[ -f "$BACKEND_DIR/.venv_linux/bin/activate" ]]; then
  # shellcheck disable=SC1090
  source "$BACKEND_DIR/.venv_linux/bin/activate"
elif command -v poetry >/dev/null 2>&1 && [[ -f "$BACKEND_DIR/pyproject.toml" ]]; then
  RUN_PREFIX=(poetry run)
else
  cat >&2 <<'EOF'
[run_api] Python environment not found.

Expected one of:
  - backend/.venv (recommended for WSL)
  - backend/.venv_linux
  - poetry available (poetry run)

Fix (WSL):
  cd backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
EOF
  exit 1
fi

cd "$BACKEND_DIR"
exec "${RUN_PREFIX[@]}" python3 -m uvicorn api.app.main:app --host 0.0.0.0 --port "$PORT" --reload
