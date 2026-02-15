<#
DEVTEST-DB-5435 — Docker start helper

Purpose:
- Start the dedicated dev/test Postgres container on port 5435.
- Uses a separate compose file: docker-compose.devtest-db.yml
- Uses a separate compose project name: wordloom-devtest

Usage:
  .\backend\scripts\devtest_db_5435_start.ps1

If you changed init scripts and need a fresh DB (DESTROYS DATA):
  docker compose -f .\docker-compose.devtest-db.yml -p wordloom-devtest down -v
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location (Join-Path $PSScriptRoot '..\..')
try {
  docker compose -f .\docker-compose.devtest-db.yml -p wordloom-devtest up -d
  docker compose -f .\docker-compose.devtest-db.yml -p wordloom-devtest ps
} finally {
  Pop-Location
}
