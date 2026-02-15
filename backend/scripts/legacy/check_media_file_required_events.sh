#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: check_media_file_required_events.sh <CID> <LOG_FILE>"
  exit 1
fi

CID="$1"
LOG_FILE="$2"

required=(
  "media.file.request_received"
  "media.file.db_loaded"
  "media.file.storage_resolved"
  "media.file.response_prepared"
  "media.file.response_sent"
  "http.response"
)

events=$(jq -R -r --arg cid "$CID" '
  fromjson?
  | select(. != null)
  | select(.correlation_id? == $cid)
  | .event? // empty
' "$LOG_FILE" | sort -u)

echo "Observed events for CID=$CID:" >&2
echo "$events" >&2

missing=0
for r in "${required[@]}"; do
  if ! grep -qx "$r" <<< "$events"; then
    echo "MISSING: $r"
    missing=1
  fi
done

if [[ $missing -eq 0 ]]; then
  echo "OK: all required events present for CID=$CID"
else
  exit 2
fi