#!/usr/bin/env bash
set -euo pipefail

# Stable shim entrypoint.
#
# Implementation lives under backend/scripts/legacy/, but Procfile/docs use this path.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/../legacy/run_worker.sh" "$@"
