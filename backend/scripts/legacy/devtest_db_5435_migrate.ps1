<#
DEVTEST-DB-5435 — Alembic migrate script (SAFE-GUARDED)

Purpose:
- Run Alembic migrations against the dedicated DEVTEST Postgres running on localhost:5435.
- Intended for:
  - wordloom_dev  (local development)
  - wordloom_test (pytest/integration)

Safety guarantees:
- This script REFUSES to run unless:
  - host is localhost/127.0.0.1
  - port is 5435
  - database name is wordloom_dev or wordloom_test

Usage:
  # migrate dev
  .\backend\scripts\devtest_db_5435_migrate.ps1 -Database wordloom_dev

  # migrate test
  .\backend\scripts\devtest_db_5435_migrate.ps1 -Database wordloom_test

Notes:
- This is intentionally separate from docker/sandbox configs.
- It does NOT read backend/.env.docker.
#>

param(
  [Parameter(Mandatory = $false)]
  [ValidateSet('wordloom_dev','wordloom_test')]
  [Alias('DbName')]
  [string]$Database = 'wordloom_test'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-PythonExe {
  if ($env:VIRTUAL_ENV) {
    $candidate = Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'
    if (Test-Path $candidate) { return $candidate }
  }

  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
  $candidate = Join-Path $repoRoot '.venv\Scripts\python.exe'
  if (Test-Path $candidate) { return $candidate }

  return 'python'
}

$PythonExe = Resolve-PythonExe

$DatabaseUrl = "postgresql+psycopg://wordloom:wordloom@localhost:5435/$Database"

function Assert-SafeDatabaseUrl([string]$Url) {
  if ($Url -notmatch '^postgresql\+psycopg://wordloom:wordloom@(localhost|127\.0\.0\.1):5435/(wordloom_dev|wordloom_test)$') {
    throw "[DEVTEST-DB-5435] Refusing to run migrations for unsafe DATABASE_URL: $Url"
  }
}

Assert-SafeDatabaseUrl -Url $DatabaseUrl

Write-Host "[DEVTEST-DB-5435] Running alembic upgrade head" -ForegroundColor Cyan
Write-Host "[DEVTEST-DB-5435] DATABASE_URL=$DatabaseUrl" -ForegroundColor DarkGray

$env:DATABASE_URL = $DatabaseUrl

# Clear Settings cache if current process already imported settings.
# (Harmless if not imported.)
try {
  $null = & $PythonExe -c "from api.app.config.setting import get_settings; get_settings.cache_clear(); print('cache_cleared')" 2>$null
} catch {
  # ignore
}

# Run alembic from backend/ so alembic.ini is found and migration paths resolve.
Push-Location (Join-Path $PSScriptRoot '..')
try {
  & $PythonExe -m alembic -c alembic.ini upgrade head
} finally {
  Pop-Location
}
