#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: trace_cid.sh <CID> <LOG_FILE>"
  echo "Example: ./scripts/trace_cid.sh 1234-... ./server.log"
  exit 1
fi

CID="$1"
LOG_FILE="$2"

jq -R -c --arg cid "$CID" '
  fromjson? 
  | select(. != null)
  | select(.correlation_id? == $cid)
  | {
      ts,
      level,
      event: (.event? // null),
      logger,
      message,
      method: (.method? // null),
      path: (.path? // null),
      status_code: (.status_code? // null),
      duration_ms: (.duration_ms? // null),
      db_duration_ms: (.db_duration_ms? // null),
      storage_duration_ms: (.storage_duration_ms? // null),
      file_size_bytes: (.file_size_bytes? // null),
      error: (.error? // null)
    }
' "$LOG_FILE"