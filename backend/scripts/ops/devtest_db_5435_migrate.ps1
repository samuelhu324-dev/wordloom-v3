<#
Stable shim for DEVTEST-DB-5435 migrate helper.

Implementation lives under backend/scripts/legacy/.
#>

param(
  [Parameter(Mandatory = $false)]
  [ValidateSet('wordloom_dev','wordloom_test')]
  [Alias('DbName')]
  [Alias('Database')]
  [string]$DatabaseName = 'wordloom_test'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$legacy = Join-Path $PSScriptRoot '..\legacy\devtest_db_5435_migrate.ps1'
if (-not (Test-Path $legacy)) {
  throw "legacy script not found: $legacy"
}

& $legacy -Database $DatabaseName
