@echo off
cd /d %~dp0
if not exist .env.pg (
  copy .env.pg.example .env.pg >nul
)
docker compose -f docker-compose.pg.yml --env-file .env.pg up -d
pause
