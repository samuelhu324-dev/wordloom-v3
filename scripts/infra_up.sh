#!/usr/bin/env bash
set -euo pipefail

# Infra runner (WSL)
# Usage:
#   ./scripts/infra_up.sh es
#   ./scripts/infra_up.sh monitoring

MODE="${1:-es}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

DOCKER_BIN="docker"
if ! command -v docker >/dev/null 2>&1; then
  if command -v docker.exe >/dev/null 2>&1; then
    DOCKER_BIN="docker.exe"
  else
    echo "[infra_up] 'docker' not found. Enable Docker Desktop WSL integration." >&2
    exit 1
  fi
fi

case "$MODE" in
  es)
    "$DOCKER_BIN" compose -f docker-compose.infra.yml up -d es
    ;;
  monitoring)
    "$DOCKER_BIN" compose -f docker-compose.infra.yml --profile monitoring up -d
    ;;
  *)
    echo "[infra_up] Unknown mode '$MODE' (expected: es|monitoring)" >&2
    exit 2
    ;;
 esac
