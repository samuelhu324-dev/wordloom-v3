<#
Stable shim for DEVTEST-DB-5435 pytest runner.

Implementation lives under backend/scripts/legacy/.
#>

param(
  [Parameter(Mandatory = $false)]
  [Alias('PytestArgs')]
  [string]$Args = "-q api/app/tests"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$legacy = Join-Path $PSScriptRoot '..\legacy\devtest_db_5435_run_pytest.ps1'
if (-not (Test-Path $legacy)) {
  throw "legacy script not found: $legacy"
}

& $legacy -Args $Args
