#!/usr/bin/env bash
set -euo pipefail

# One-command app runner (WSL)
# Starts: API + outbox worker + Next.js
# Usage:
#   ./scripts/app_up.sh dev
#   ./scripts/app_up.sh test
#   ./scripts/app_up.sh test --no-worker

ENV_NAME="${1:-dev}"
shift || true

NO_WORKER=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-worker)
      NO_WORKER=1
      shift
      ;;
    *)
      echo "[app_up] Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

case "$ENV_NAME" in
  dev)
    ENV_FILE="$REPO_ROOT/.env.dev"
    PROCFILE="$REPO_ROOT/Procfile.dev"
    ;;
  test)
    ENV_FILE="$REPO_ROOT/.env.test"
    PROCFILE="$REPO_ROOT/Procfile.test"
    ;;
  *)
    echo "[app_up] Unknown env '$ENV_NAME' (expected: dev|test)" >&2
    exit 2
    ;;
 esac

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[app_up] env file not found: $ENV_FILE" >&2
  exit 1
fi

if [[ ! -f "$PROCFILE" ]]; then
  echo "[app_up] Procfile not found: $PROCFILE" >&2
  exit 1
fi

HONCHO=(honcho)
if ! command -v honcho >/dev/null 2>&1; then
  if python3 -m honcho --help >/dev/null 2>&1; then
    HONCHO=(python3 -m honcho)
  else
    cat >&2 <<'EOF'
[app_up] 'honcho' not found.

Install in WSL (recommended):
  python3 -m pip install --user honcho

Or via pipx:
  sudo apt-get update && sudo apt-get install -y pipx
  pipx install honcho
EOF
    exit 1
  fi
fi

# Export env vars to all Procfile processes.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

cd "$REPO_ROOT"
echo "[app_up] Starting app processes ($ENV_NAME) via $(basename "$PROCFILE")"

if [[ "$NO_WORKER" == "1" ]]; then
  echo "[app_up] --no-worker: starting only api + ui"
  exec "${HONCHO[@]}" start -f "$PROCFILE" api ui
fi

exec "${HONCHO[@]}" start -f "$PROCFILE"
