#!/usr/bin/env bash
set -euo pipefail

# Labs-005 / Experiment 5
# Validate outbox failure management for Chronicle worker:
#   - transient -> pending + next_retry_at
#   - deterministic -> failed + error_reason
#   - manual fix + replay -> pending -> done
#
# Usage (WSL2):
#   ./backend/scripts/ops_labs_005_chronicle_e5_failure.sh .env.test

ENV_FILE="${1:-}"

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

if ! command -v psql >/dev/null 2>&1; then
  echo "ERR: psql not found." >&2
  echo "Install (WSL2): sudo apt-get update && sudo apt-get install -y postgresql-client" >&2
  exit 2
fi

# Avoid getting stuck in a pager.
export PSQL_PAGER=off
export PAGER=cat

# Write an evidence snapshot for repeatability.
SNAP_DIR="$REPO_ROOT/docs/architecture/runbook/labs/_snapshots"
mkdir -p "$SNAP_DIR"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT="$SNAP_DIR/labs-005-chronicle-e5-failure-$TS.txt"
exec > >(tee "$OUT") 2>&1

# Convert SQLAlchemy URL to libpq URL for psql.
PSQL_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

psql_one() {
  local sql="$1"
  psql "$PSQL_URL" -X -qAt -v ON_ERROR_STOP=1 -c "$sql" | head -n 1 | tr -d '\r'
}

cd "$BACKEND_DIR"
if [[ -f "$BACKEND_DIR/.venv_linux/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/.venv_linux/bin/activate"
fi

echo "[labs-005/e5] db=$DATABASE_URL"

echo "[labs-005/e5] Pick one real chronicle_event id for transient injection"
GOOD_EVENT_ID="$(psql_one "select id from chronicle_events order by occurred_at desc, id desc limit 1;")"
if [[ -z "$GOOD_EVENT_ID" ]]; then
  echo "ERR: No rows in chronicle_events; create at least one event first." >&2
  exit 2
fi
echo "[labs-005/e5] good_event_id=$GOOD_EVENT_ID"

echo "[labs-005/e5] Insert 1 deterministic outbox row (invalid op)"
DET_OUTBOX_ID="$(psql_one "insert into chronicle_outbox_events (id, entity_type, entity_id, op, event_version, created_at, status, attempts, updated_at, replay_count) values (gen_random_uuid(), 'chronicle_event', gen_random_uuid(), 'not-a-real-op', 0, now(), 'pending', 0, now(), 0) returning id;")"
echo "[labs-005/e5] det_outbox_id=$DET_OUTBOX_ID"

echo "[labs-005/e5] Insert 1 transient outbox row (valid op)"
TR_OUTBOX_ID="$(psql_one "insert into chronicle_outbox_events (id, entity_type, entity_id, op, event_version, created_at, status, attempts, updated_at, replay_count) values (gen_random_uuid(), 'chronicle_event', '$GOOD_EVENT_ID', 'upsert', 0, now(), 'pending', 0, now(), 0) returning id;")"
echo "[labs-005/e5] tr_outbox_id=$TR_OUTBOX_ID"

echo "[labs-005/e5] Run worker with transient fault injection (should schedule retry)"
export OUTBOX_RUN_SECONDS=2
export OUTBOX_WORKER_ID="${OUTBOX_WORKER_ID:-e5}"
export OUTBOX_METRICS_PORT="${CHRONICLE_OUTBOX_METRICS_PORT:-9111}"
# Make the transient phase demonstrably "retry scheduled" (pending + next_retry_at)
# instead of exhausting attempts within a single short run.
export OUTBOX_MAX_ATTEMPTS=10
export OUTBOX_BASE_BACKOFF_SECONDS=5
export OUTBOX_MAX_BACKOFF_SECONDS=5
export OUTBOX_POLL_INTERVAL_SECONDS=0.2
export OUTBOX_BATCH_SIZE=25

export OUTBOX_FAULT_INJECT_KIND=transient
export OUTBOX_FAULT_INJECT_ENTITY_ID="$GOOD_EVENT_ID"

python3 scripts/chronicle_outbox_worker.py || true

unset OUTBOX_FAULT_INJECT_KIND
unset OUTBOX_FAULT_INJECT_ENTITY_ID

echo "[labs-005/e5] Verify transient row is pending with next_retry_at and reason=unknown_exception"
psql "$PSQL_URL" -c "select id, status, attempts, error_reason, (next_retry_at is not null) as has_next_retry_at from chronicle_outbox_events where id='$TR_OUTBOX_ID';"

echo "[labs-005/e5] Run worker again without injection (should converge to done)"
export OUTBOX_RUN_SECONDS=10
python3 scripts/chronicle_outbox_worker.py || true

echo "[labs-005/e5] Verify transient row is done"
psql "$PSQL_URL" -c "select id, status, attempts, error_reason from chronicle_outbox_events where id='$TR_OUTBOX_ID';"

echo "[labs-005/e5] Verify deterministic row is failed (reason=deterministic_exception)"
psql "$PSQL_URL" -c "select id, status, attempts, error_reason, left(error, 120) as error_snip from chronicle_outbox_events where id='$DET_OUTBOX_ID';"

echo "[labs-005/e5] Apply manual fix (change op/entity_id to a valid upsert)"
psql "$PSQL_URL" -c "update chronicle_outbox_events set op='upsert', entity_id='$GOOD_EVENT_ID', updated_at=now() where id='$DET_OUTBOX_ID';"

echo "[labs-005/e5] Replay failed -> pending (writes audit fields)"
python3 scripts/chronicle_outbox_replay_failed.py --by ops --reason "labs-005 e5 manual fix" --limit 1 --ids "$DET_OUTBOX_ID"

echo "[labs-005/e5] Process replayed row"
export OUTBOX_RUN_SECONDS=10
python3 scripts/chronicle_outbox_worker.py || true

echo "[labs-005/e5] Verify deterministic row is now done and replay audit fields are set"
psql "$PSQL_URL" -c "select id, status, replay_count, last_replayed_by, (last_replayed_at is not null) as has_last_replayed_at from chronicle_outbox_events where id='$DET_OUTBOX_ID';"

echo "[labs-005/e5] OK"
echo "[labs-005/e5] snapshot written: $OUT"
