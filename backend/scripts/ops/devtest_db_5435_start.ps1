<#
Stable shim for DEVTEST-DB-5435 start helper.

Implementation lives under backend/scripts/legacy/.
This shim exists so docs and WSL wrappers can keep using backend/scripts/*.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$legacy = Join-Path $PSScriptRoot '..\legacy\devtest_db_5435_start.ps1'
if (-not (Test-Path $legacy)) {
  throw "legacy script not found: $legacy"
}

& $legacy @args
