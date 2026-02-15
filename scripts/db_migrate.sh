#!/usr/bin/env bash
set -euo pipefail

# Migrate dev/test DB on localhost:5435 safely (guarded).
# Usage:
#   ./scripts/db_migrate.sh dev
#   ./scripts/db_migrate.sh test

ENV_NAME="${1:-test}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_DIR="$REPO_ROOT/backend"

case "$ENV_NAME" in
  dev) DB_NAME="wordloom_dev" ;;
  test) DB_NAME="wordloom_test" ;;
  *)
    echo "[db_migrate] Unknown env '$ENV_NAME' (expected: dev|test)" >&2
    exit 2
    ;;
esac

DATABASE_URL="postgresql+psycopg://wordloom:wordloom@localhost:5435/$DB_NAME"

assert_safe_database_url() {
  local url="$1"
  if [[ ! "$url" =~ ^postgresql\+psycopg://wordloom:wordloom@(localhost|127\.0\.0\.1):5435/(wordloom_dev|wordloom_test)$ ]]; then
    echo "[db_migrate] Refusing to run migrations for unsafe DATABASE_URL: $url" >&2
    return 1
  fi
}

assert_safe_database_url "$DATABASE_URL" || exit 1

activate=""
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  activate=""
elif [[ -f "$BACKEND_DIR/.venv_linux/bin/activate" ]]; then
  activate="$BACKEND_DIR/.venv_linux/bin/activate"
elif [[ -f "$BACKEND_DIR/.venv/bin/activate" ]]; then
  activate="$BACKEND_DIR/.venv/bin/activate"
fi

if [[ -n "$activate" || -n "${VIRTUAL_ENV:-}" ]]; then
  (
    set -euo pipefail
    if [[ -n "$activate" ]]; then
      # shellcheck disable=SC1090
      source "$activate"
    fi

    export DATABASE_URL
    cd "$BACKEND_DIR"
    echo "[db_migrate] Running alembic upgrade head (WSL)"
    echo "[db_migrate] DATABASE_URL=$DATABASE_URL" >&2
    python3 -m alembic -c alembic.ini upgrade head
  )
  exit 0
fi

if ! command -v wslpath >/dev/null 2>&1; then
  echo "[db_migrate] wslpath not found; expected to run inside WSL." >&2
  exit 1
fi

POWERSHELL_BIN="powershell.exe"
if ! command -v "$POWERSHELL_BIN" >/dev/null 2>&1; then
  if command -v pwsh.exe >/dev/null 2>&1; then
    POWERSHELL_BIN="pwsh.exe"
  else
    echo "[db_migrate] Unable to find powershell.exe or pwsh.exe from WSL." >&2
    exit 1
  fi
fi

PS1_PATH_WIN="$(wslpath -w "$REPO_ROOT/backend/scripts/ops/devtest_db_5435_migrate.ps1")"
"$POWERSHELL_BIN" -NoProfile -ExecutionPolicy Bypass -File "$PS1_PATH_WIN" -Database "$DB_NAME"
