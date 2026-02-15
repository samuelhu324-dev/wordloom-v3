#!/usr/bin/env bash
set -euo pipefail

# Minimal smoke checks for outbox worker runtime endpoints.
# - /metrics already exists today (Prometheus exporter)
# - /healthz and /readyz are placeholders for the v4 hardening described in log-S0B

METRICS_PORT="${OUTBOX_METRICS_PORT:-9109}"
HTTP_PORT="${OUTBOX_HTTP_PORT:-9112}"

echo "[s0b] Checking /metrics on :${METRICS_PORT} ..."
if curl -fsS "http://localhost:${METRICS_PORT}/metrics" >/dev/null; then
  echo "[s0b] /metrics OK"
else
  echo "[s0b] /metrics FAILED" >&2
  exit 1
fi

echo "[s0b] Sampling outbox_* metric names (best-effort) ..."
# Don't fail the script if a specific metric isn't present yet; just show what's there.
curl -fsS "http://localhost:${METRICS_PORT}/metrics" \
  | awk -F'{' '/^outbox_[a-zA-Z0-9_]+/{print $1}' \
  | sort -u \
  | head -n 50 \
  || true

echo "[s0b] Checking future endpoints on :${HTTP_PORT} (expected to fail until implemented) ..."
set +e
curl -fsS "http://localhost:${HTTP_PORT}/healthz"; echo
echo "[s0b] /healthz exit=$?"
curl -fsS "http://localhost:${HTTP_PORT}/readyz"; echo
echo "[s0b] /readyz exit=$?"
set -e

echo "[s0b] Done."