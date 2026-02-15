#!/usr/bin/env bash
set -euo pipefail

# Stable shim entrypoint.
#
# This repo keeps historical/legacy implementations under backend/scripts/legacy/,
# but Procfile/docs expect a stable path under backend/scripts/.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/../legacy/run_api.sh" "$@"
