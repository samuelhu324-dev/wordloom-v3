#!/usr/bin/env bash
set -euo pipefail

# Run outbox worker with env file (.env.dev/.env.test).
# Usage:
#   ./backend/scripts/ops/run_worker.sh ../.env.dev

ENV_FILE="${1:-../.env.dev}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
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
[run_worker] Python environment not found.

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

# Some WSL setups have a user-site `sitecustomize.py` that forces an interactive
# console (">>>") on startup. This breaks long-running workers.
# Disable user site-packages for this process to avoid importing it.
export PYTHONNOUSERSITE=1

exec "${RUN_PREFIX[@]}" python3 scripts/search_outbox_worker.py
