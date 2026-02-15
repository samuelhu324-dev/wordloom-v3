<#
DEVTEST-DB-5435 — Pytest runner (SAFE-GUARDED)

Purpose:
- Ensure the DEVTEST Postgres test DB is migrated, then run pytest.
- Keeps test runs explicitly pinned to localhost:5435/wordloom_test so we never
  accidentally hit docker/sandbox databases.

Usage:
  .\backend\scripts\devtest_db_5435_run_pytest.ps1

Optional:
  .\backend\scripts\devtest_db_5435_run_pytest.ps1 -Args "-q api/app/tests"
#>

param(
  [Parameter(Mandatory = $false)]
  [Alias('PytestArgs')]
  [string]$Args = "-q api/app/tests"
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

# 1) Migrate test DB
& "$PSScriptRoot\devtest_db_5435_migrate.ps1" -Database wordloom_test

# 2) Run pytest pinned to wordloom_test
$env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test"
Write-Host "[DEVTEST-DB-5435] pytest $Args" -ForegroundColor Cyan

Push-Location (Join-Path $PSScriptRoot '..')
try {
  $PytestArgv = @()
  if ($Args -and $Args.Trim() -ne "") {
    $PytestArgv = $Args -split "\s+"
  }

  # Script runs from backend/; allow callers to pass paths starting with backend/.
  for ($i = 0; $i -lt $PytestArgv.Count; $i++) {
    if ($PytestArgv[$i] -match '^(backend)[\\/](.+)$') {
      $PytestArgv[$i] = $Matches[2]
    }
  }

  & $PythonExe -m pytest @PytestArgv
} finally {
  Pop-Location
}
