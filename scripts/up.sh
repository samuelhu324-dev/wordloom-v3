#!/usr/bin/env bash
set -euo pipefail

# One-command runner (WSL): infra + db + migrate + app
# Usage:
#   ./scripts/up.sh dev
#   ./scripts/up.sh test
#   ./scripts/up.sh test --no-worker

ENV_NAME="${1:-dev}"
shift || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

"$REPO_ROOT/scripts/preflight.sh" "$ENV_NAME"

echo "[up] Bringing up infra (es)"

"$REPO_ROOT/scripts/infra_up.sh" es

echo "[up] Bringing up dev/test db (localhost:5435)"
"$REPO_ROOT/scripts/db_up.sh"

echo "[up] Migrating database ($ENV_NAME)"
"$REPO_ROOT/scripts/db_migrate.sh" "$ENV_NAME"

echo "[up] Starting app (this stays running; Ctrl+C to stop)"
"$REPO_ROOT/scripts/app_up.sh" "$ENV_NAME" "$@"
