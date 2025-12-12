#!/bin/sh
# filepath: backend/entrypoint.sh
set -e

cd /app

echo "[entrypoint] Running database migrations"
python -m alembic upgrade head

echo "[entrypoint] Starting application"
exec "$@"