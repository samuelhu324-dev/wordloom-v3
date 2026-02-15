<#
DEVTEST-DB-5435 — Docker stop helper

Usage:
  .\backend\scripts\devtest_db_5435_stop.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location (Join-Path $PSScriptRoot '..\..')
try {
  docker compose -f .\docker-compose.devtest-db.yml -p wordloom-devtest down
} finally {
  Pop-Location
}
