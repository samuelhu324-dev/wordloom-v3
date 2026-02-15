#!/usr/bin/env bash
set -euo pipefail

# Capture wrapper for Labs-004 Experiment 6 (v4 runtime):
# Runs the experiment and writes a snapshot under docs/architecture/runbook/labs/_snapshots.

REPO_ROOT_DIR=${REPO_ROOT_DIR:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
cd "$REPO_ROOT_DIR"

SNAP_DIR="docs/architecture/runbook/labs/_snapshots"
mkdir -p "$SNAP_DIR"
TS="$(date +%Y%m%dT%H%M%S)"
SNAP="$SNAP_DIR/labs-004-v4-runtime-search-worker-$TS.txt"

{
  echo "# labs-004 experiment 6 (v4) runtime"
  echo "# started_at=$(date -Is)"
  echo "# OUTBOX_METRICS_PORT=${OUTBOX_METRICS_PORT:-}" \
       "OUTBOX_HTTP_PORT=${OUTBOX_HTTP_PORT:-}" \
       "OUTBOX_SHUTDOWN_GRACE_SECONDS=${OUTBOX_SHUTDOWN_GRACE_SECONDS:-}" \
       "OUTBOX_REQUIRE_ES_READY=${OUTBOX_REQUIRE_ES_READY:-}"
  echo
  bash backend/scripts/ops_labs_004_v4_runtime_search_worker.sh
  echo
  echo "SNAPSHOT=$SNAP"
} 2>&1 | tee "$SNAP"
