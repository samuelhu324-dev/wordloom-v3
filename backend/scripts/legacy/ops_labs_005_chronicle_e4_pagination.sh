#!/usr/bin/env bash
set -euo pipefail

# Labs-005 experiment 4 runner (time/pagination stability checks).
#
# Usage (WSL2):
#   ./backend/scripts/ops_labs_005_chronicle_e4_pagination.sh .env.test

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
  echo "     Install (WSL2): sudo apt-get update && sudo apt-get install -y postgresql-client" >&2
  exit 2
fi

# Convert SQLAlchemy URL to libpq URL for psql.
PSQL_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

SNAP_DIR="$REPO_ROOT/docs/architecture/runbook/labs/_snapshots"
mkdir -p "$SNAP_DIR"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT="$SNAP_DIR/labs-005-chronicle-e4-pagination-$TS.txt"

{
  echo "=== labs-005 snapshot ==="
  echo "ts=$TS"
  echo "mode=e4_pagination"
  echo

  echo "-- entries occurred_at range + total"
  psql "$PSQL_URL" -v ON_ERROR_STOP=1 <<'SQL'
select
  min(occurred_at) as min_occurred_at,
  max(occurred_at) as max_occurred_at,
  count(*) as entries
from chronicle_entries;
SQL
  echo

  echo "-- duplicate occurred_at buckets (shows why (occurred_at,id) tie-breaker is needed)"
  psql "$PSQL_URL" -v ON_ERROR_STOP=1 <<'SQL'
select occurred_at, count(*) as n
from chronicle_entries
group by 1
having count(*) > 1
order by n desc, occurred_at desc
limit 10;
SQL
  echo

  echo "-- cursor pagination check using (occurred_at, id)"
  echo "-- Expect: overlap_n = 0"
  psql "$PSQL_URL" -v ON_ERROR_STOP=1 <<'SQL'
with
  page1 as (
    select id, occurred_at
    from chronicle_entries
    order by occurred_at desc, id desc
    limit 20
  ),
  cursor as (
    select occurred_at as c_occ, id as c_id
    from page1
    order by occurred_at asc, id asc
    limit 1
  ),
  page2 as (
    select id, occurred_at
    from chronicle_entries
    where (occurred_at, id) < (select c_occ, c_id from cursor)
    order by occurred_at desc, id desc
    limit 20
  )
select
  (select count(*) from page1) as page1_n,
  (select count(*) from page2) as page2_n,
  (select count(*) from (select id from page1 intersect select id from page2) s) as overlap_n;
SQL
} | tee "$OUT"

echo "[labs-005] snapshot written: $OUT"