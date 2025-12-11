#!/usr/bin/env bash
set -euo pipefail

cd /app

echo "[entrypoint] Running database migrations"
python -m alembic upgrade head

echo "[entrypoint] Starting application"
exec "$@"
