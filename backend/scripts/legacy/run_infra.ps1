<#
Run infra-only compose (Elasticsearch + optional monitoring)

Usage:
  .\backend\scripts\run_infra.ps1
  .\backend\scripts\run_infra.ps1 -Monitoring

#>

param(
  [switch]$Monitoring
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$compose = Join-Path $repoRoot 'docker-compose.infra.yml'

if (-not (Test-Path $compose)) {
  throw "compose file not found: $compose"
}

Push-Location $repoRoot
try {
  if ($Monitoring) {
    docker compose -f $compose --profile monitoring up -d
  } else {
    docker compose -f $compose up -d es
  }
} finally {
  Pop-Location
}
