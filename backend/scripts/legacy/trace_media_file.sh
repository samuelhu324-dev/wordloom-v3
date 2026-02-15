#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: trace_media_file.sh <LOG_FILE>"
  echo "Example: ./scripts/trace_media_file.sh ./server.log"
  exit 1
fi

LOG_FILE="$1"

jq -R -c '
  fromjson?
  | select(. != null)
  | select((.event? // .message // "") | test("media\\.file\\.")) 
  | {ts, level, correlation_id: (.correlation_id? // null), event: (.event? // null), logger, message, duration_ms: (.duration_ms? // null), db_duration_ms: (.db_duration_ms? // null), storage_duration_ms: (.storage_duration_ms? // null), file_size_bytes: (.file_size_bytes? // null), status_code: (.status_code? // null)}
' "$LOG_FILE"