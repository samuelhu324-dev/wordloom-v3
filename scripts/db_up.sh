#!/usr/bin/env bash
set -euo pipefail

# Start dev/test Postgres on localhost:5435 (Docker Desktop) from WSL.
# Usage:
#   ./scripts/db_up.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DOCKER_BIN="docker"
if ! command -v docker >/dev/null 2>&1; then
	if command -v docker.exe >/dev/null 2>&1; then
		DOCKER_BIN="docker.exe"
	else
		DOCKER_BIN=""
	fi
fi

if [[ -n "$DOCKER_BIN" ]]; then
	cd "$REPO_ROOT"
	"$DOCKER_BIN" compose -f docker-compose.devtest-db.yml -p wordloom-devtest up -d

	# Wait for healthcheck (best-effort; fail with actionable output).
	cid="$($DOCKER_BIN compose -f docker-compose.devtest-db.yml -p wordloom-devtest ps -q db_devtest 2>/dev/null | tr -d '\r' | head -n 1)"
	if [[ -n "${cid:-}" ]]; then
		deadline=$((SECONDS + 90))
		while (( SECONDS < deadline )); do
			status="$($DOCKER_BIN inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null | tr -d '\r' || true)"
			if [[ "$status" == "healthy" ]]; then
				echo "[db_up] DB is healthy (localhost:5435)"
				exit 0
			fi
			if [[ "$status" == "unhealthy" ]]; then
				echo "[db_up] DB container is unhealthy; showing logs" >&2
				$DOCKER_BIN logs --tail 200 "$cid" >&2 || true
				exit 1
			fi
			sleep 2
		done

		echo "[db_up] Timed out waiting for DB healthcheck; showing status/logs" >&2
		$DOCKER_BIN compose -f docker-compose.devtest-db.yml -p wordloom-devtest ps >&2 || true
		$DOCKER_BIN logs --tail 200 "$cid" >&2 || true
		exit 1
	fi

	# If we couldn't resolve the container ID, still continue (compose already ran).
	exit 0
fi

if ! command -v wslpath >/dev/null 2>&1; then
	echo "[db_up] wslpath not found; expected to run inside WSL." >&2
	exit 1
fi

POWERSHELL_BIN="powershell.exe"
if ! command -v "$POWERSHELL_BIN" >/dev/null 2>&1; then
	if command -v pwsh.exe >/dev/null 2>&1; then
		POWERSHELL_BIN="pwsh.exe"
	else
		echo "[db_up] Unable to find powershell.exe or pwsh.exe from WSL." >&2
		exit 1
	fi
fi

PS1_PATH_WIN="$(wslpath -w "$REPO_ROOT/backend/scripts/ops/devtest_db_5435_start.ps1")"
"$POWERSHELL_BIN" -NoProfile -ExecutionPolicy Bypass -File "$PS1_PATH_WIN"
