#!/usr/bin/env bash
set -euo pipefail

# Labs-005 runner (Chronicle projection validation).
#
# Usage (WSL2):
#   ./backend/scripts/ops_labs_005_chronicle.sh .env.test sync
#   ./backend/scripts/ops_labs_005_chronicle.sh .env.test outbox 20
#   CHRONICLE_PROJECTION_VERSION=2 ./backend/scripts/ops_labs_005_chronicle.sh .env.test sync
#
# Requirements (WSL2):
#   - backend/.venv_linux created (recommended: python3 -m venv --copies backend/.venv_linux)
#   - Optional: psql installed (sudo apt-get install -y postgresql-client)

ENV_FILE="${1:-}"
MODE="${2:-sync}"       # sync | outbox
RUN_SECONDS="${3:-15}"  # only used in outbox mode

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

if [[ -z "$ENV_FILE" ]]; then
  echo "ERR: ENV file is required, e.g. .env.test" >&2
  exit 2
fi

cd "$REPO_ROOT"

if [[ "$ENV_FILE" != /* ]]; then
  ENV_FILE="$REPO_ROOT/$ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERR: env file not found: $ENV_FILE" >&2
  exit 2
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERR: DATABASE_URL is not set after sourcing $ENV_FILE" >&2
  exit 2
fi

HAVE_PSQL=1
if ! command -v psql >/dev/null 2>&1; then
  HAVE_PSQL=0
  echo "WARN: psql not found; snapshots will be skipped." >&2
  echo "      Install (WSL2): sudo apt-get update && sudo apt-get install -y postgresql-client" >&2
fi

cd "$BACKEND_DIR"

# Prefer repo venv.
if [[ -f "$BACKEND_DIR/.venv_linux/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/.venv_linux/bin/activate"
fi

echo "[labs-005] mode=$MODE db=$DATABASE_URL"

case "$MODE" in
  sync)
    python3 scripts/rebuild_chronicle_entries.py --truncate
    ;;
  outbox)
    python3 scripts/rebuild_chronicle_entries.py --truncate --emit-outbox

    export OUTBOX_RUN_SECONDS="$RUN_SECONDS"
    export OUTBOX_WORKER_ID="${OUTBOX_WORKER_ID:-c1}"

    # Important: .env.test is primarily for the search worker and sets OUTBOX_METRICS_PORT=9109.
    # For chronicle labs, use a separate default port to avoid conflicts.
    export OUTBOX_METRICS_PORT="${CHRONICLE_OUTBOX_METRICS_PORT:-9110}"

    # Conservative defaults.
    export OUTBOX_BATCH_SIZE="${OUTBOX_BATCH_SIZE:-50}"
    export OUTBOX_POLL_INTERVAL_SECONDS="${OUTBOX_POLL_INTERVAL_SECONDS:-0.2}"
    export OUTBOX_LEASE_SECONDS="${OUTBOX_LEASE_SECONDS:-30}"
    export OUTBOX_MAX_ATTEMPTS="${OUTBOX_MAX_ATTEMPTS:-10}"
    export OUTBOX_BASE_BACKOFF_SECONDS="${OUTBOX_BASE_BACKOFF_SECONDS:-0.5}"
    export OUTBOX_MAX_BACKOFF_SECONDS="${OUTBOX_MAX_BACKOFF_SECONDS:-10}"
    export OUTBOX_RECLAIM_INTERVAL_SECONDS="${OUTBOX_RECLAIM_INTERVAL_SECONDS:-5}"
    export OUTBOX_MAX_PROCESSING_SECONDS="${OUTBOX_MAX_PROCESSING_SECONDS:-600}"

    python3 scripts/chronicle_outbox_worker.py
    ;;
  *)
    echo "ERR: unknown mode: $MODE (expected sync|outbox)" >&2
    exit 2
    ;;
esac

if [[ "$HAVE_PSQL" != "1" ]]; then
  exit 0
fi

# Convert SQLAlchemy URL to libpq URL for psql.
PSQL_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

SNAP_DIR="$REPO_ROOT/docs/architecture/runbook/labs/_snapshots"
mkdir -p "$SNAP_DIR"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT="$SNAP_DIR/labs-005-chronicle-$MODE-$TS.txt"

{
  echo "=== labs-005 snapshot ==="
  echo "ts=$TS"
  echo "mode=$MODE"
  echo "CHRONICLE_PROJECTION_VERSION=${CHRONICLE_PROJECTION_VERSION-}" 
  if [[ "$MODE" == "sync" ]]; then
    echo "note=sync rebuild does not consume chronicle_outbox_events; outbox counts reflect prior runs"
  fi
  echo

  echo "-- outbox status distribution"
  psql "$PSQL_URL" -c "select status, count(*) from chronicle_outbox_events group by 1 order by 1;" 2>/dev/null || true
  echo

  echo "-- entries count"
  psql "$PSQL_URL" -c "select count(*) from chronicle_entries;" 2>/dev/null || true
  echo

  echo "-- recent entries (stable ordering: occurred_at, id)"
  psql "$PSQL_URL" -c "select id, event_type, book_id, block_id, actor_id, occurred_at, projection_version from chronicle_entries order by occurred_at desc, id desc limit 20;" 2>/dev/null || true
  echo

  echo "-- projection status"
  psql "$PSQL_URL" -c "select * from projection_status where projection_name = 'chronicle_events_to_entries';" 2>/dev/null || true
  echo

  echo "-- outbox -> event -> entry sample"
  psql "$PSQL_URL" -c "select o.status, o.entity_type, o.entity_id, e.event_type, en.summary from chronicle_outbox_events o left join chronicle_events e on e.id=o.entity_id left join chronicle_entries en on en.id=o.entity_id order by o.created_at desc limit 20;" 2>/dev/null || true
  echo

  echo "-- envelope null rates (Phase C)"
  psql "$PSQL_URL" -c "select count(*) as total, count(*) filter (where correlation_id is null) as correlation_id_null, count(*) filter (where source is null) as source_null, count(*) filter (where actor_kind is null) as actor_kind_null from chronicle_events;" 2>/dev/null || true
} | tee "$OUT"

echo "[labs-005] snapshot written: $OUT"
