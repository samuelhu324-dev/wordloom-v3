#!/usr/bin/env bash
set -euo pipefail

# Preflight checks for the WSL one-command runner.
# Usage:
#   ./scripts/preflight.sh dev|test

ENV_NAME="${1:-dev}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

_err() {
  echo "[preflight] $*" >&2
}

_require_cmd() {
  local cmd="$1"
  local help="$2"

  if ! command -v "$cmd" >/dev/null 2>&1; then
    _err "Missing '$cmd'."
    _err "$help"
    return 1
  fi
}

_check_port_free() {
  local port="$1"
  local label="$2"

  # Check Linux/WSL side.
  if command -v ss >/dev/null 2>&1; then
    if ss -ltn 2>/dev/null | grep -qE "[:.]${port}[[:space:]]"; then
      _err "Port ${port} (${label}) is already in use inside WSL."
      _err "Find it: ss -ltnp | grep ':${port}'"
      return 1
    fi
  fi

  # Check Windows host side (WSL localhost-forwarding can be blocked).
  if command -v powershell.exe >/dev/null 2>&1; then
    local pid
    pid="$(
      powershell.exe -NoProfile -Command "(Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess" 2>/dev/null \
        | tr -d '\r' \
        | tr -d '\n'
    )"
    if [[ -n "${pid:-}" && "${pid}" != "0" ]]; then
      _err "Port ${port} (${label}) is already in use on Windows host (PID ${pid})."
      _err "Find it: powershell.exe -NoProfile -Command \"Get-Process -Id ${pid}\""
      _err "Stop it:  powershell.exe -NoProfile -Command \"Stop-Process -Id ${pid} -Force\""
      return 1
    fi
  fi
}

_require_python_imports() {
  local backend_dir="$1"
  shift

  local activate=""
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    activate=""
  elif [[ -f "$backend_dir/.venv_linux/bin/activate" ]]; then
    activate="$backend_dir/.venv_linux/bin/activate"
  elif [[ -f "$backend_dir/.venv/bin/activate" ]]; then
    activate="$backend_dir/.venv/bin/activate"
  fi

  if [[ -z "$activate" && -z "${VIRTUAL_ENV:-}" ]]; then
    _err "Python environment not found under backend/ (.venv or .venv_linux)."
    _err "Fix (WSL): cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    return 1
  fi

  (
    set -euo pipefail
    if [[ -n "$activate" ]]; then
      # shellcheck disable=SC1090
      source "$activate"
    fi

    python3 - <<'PY' "$@" >/dev/null 2>&1
import importlib
import sys

missing = []
for name in sys.argv[1:]:
    try:
        importlib.import_module(name)
    except Exception:
        missing.append(name)

if missing:
    raise SystemExit("Missing modules: " + ", ".join(missing))
PY
  ) || {
    _err "Missing Python dependencies for enabled features."
    _err "Fix (WSL): cd backend && source .venv/bin/activate (or .venv_linux) && pip install -r requirements.txt"
    return 1
  }
}

if [[ -z "${WSL_DISTRO_NAME:-}" ]] && ! grep -qi microsoft /proc/version 2>/dev/null; then
  _err "This runner is designed for WSL2."
  _err "If you're on Windows PowerShell, run inside WSL: wsl -e bash"
  exit 1
fi

_require_cmd wslpath "Run this from WSL2 (wslpath should exist)." || exit 1

if ! command -v docker >/dev/null 2>&1 && ! command -v docker.exe >/dev/null 2>&1; then
  _err "Missing 'docker' in WSL."
  _err "Enable Docker Desktop WSL integration, or install docker-cli in WSL."
  exit 1
fi

if ! command -v powershell.exe >/dev/null 2>&1 && ! command -v pwsh.exe >/dev/null 2>&1; then
  _err "Cannot find 'powershell.exe' (or 'pwsh.exe') from WSL."
  _err "Enable Windows PATH integration in WSL, or ensure PowerShell is installed."
  exit 1
fi

case "$ENV_NAME" in
  dev|test) ;;
  *)
    _err "Unknown env '$ENV_NAME' (expected: dev|test)"
    exit 2
    ;;
esac

if [[ ! -f "$REPO_ROOT/.env.$ENV_NAME" ]]; then
  _err "Missing env file: $REPO_ROOT/.env.$ENV_NAME"
  exit 1
fi

if [[ ! -f "$REPO_ROOT/Procfile.$ENV_NAME" ]]; then
  _err "Missing Procfile: $REPO_ROOT/Procfile.$ENV_NAME"
  exit 1
fi

if ! command -v honcho >/dev/null 2>&1; then
  if ! python3 -m honcho --help >/dev/null 2>&1; then
    _err "Missing 'honcho' (Procfile runner)."
    _err "Install in WSL: python3 -m pip install --user honcho"
    exit 1
  fi
fi

# Load ports from env file and fail fast on conflicts.
(
  set -a
  # shellcheck disable=SC1090
  source "$REPO_ROOT/.env.$ENV_NAME"
  set +a

  : "${API_PORT:?Missing API_PORT in .env.$ENV_NAME}"
  : "${OUTBOX_METRICS_PORT:?Missing OUTBOX_METRICS_PORT in .env.$ENV_NAME}"

  # Dev/test Postgres runs on Windows host port 5435.
  _check_port_free "5435" "devtest db" || exit 1

  _check_port_free "$API_PORT" "api" || exit 1
  _check_port_free "$OUTBOX_METRICS_PORT" "outbox metrics" || exit 1

  # UI is fixed in frontend scripts.
  _check_port_free "30002" "frontend ui" || exit 1

  if [[ "${WORDLOOM_TRACING_ENABLED:-}" == "1" ]]; then
    _require_python_imports "$REPO_ROOT/backend" \
      opentelemetry.exporter.otlp.proto.http.trace_exporter \
      opentelemetry.instrumentation.fastapi \
      opentelemetry.instrumentation.httpx \
      opentelemetry.instrumentation.sqlalchemy || exit 1
  fi
)

echo "[preflight] OK ($ENV_NAME)"
