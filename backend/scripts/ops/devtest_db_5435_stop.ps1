<#
Stable shim for DEVTEST-DB-5435 stop helper.

Implementation lives under backend/scripts/legacy/.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$legacy = Join-Path $PSScriptRoot '..\legacy\devtest_db_5435_stop.ps1'
if (-not (Test-Path $legacy)) {
  throw "legacy script not found: $legacy"
}

& $legacy @args
