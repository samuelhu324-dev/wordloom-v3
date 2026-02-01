<#
Two-stage search smoke test (Elastic Stage1 + Postgres Stage2).

What it does:
1) Ensure DEVTEST Postgres is running (assumes you started it already).
2) Ensure Elasticsearch container is running on localhost:9200.
3) Backfill ES index from Postgres search_index (stores event_version).
4) Start backend (uvicorn) in WSL with SEARCH_STAGE1_PROVIDER=elastic.
5) Wait for /api/v1/health to become 200.
6) Call /api/v1/search/blocks/two-stage and print response.
7) Print a log excerpt proving Stage1 provider + Elastic recall ran.

Usage:
  .\backend\scripts\smoke_two_stage_elastic.ps1

Optional:
  .\backend\scripts\smoke_two_stage_elastic.ps1 -Port 30001 -Query "quantum" -KeepRunning

Notes:
- This uses WSL to run uvicorn because many dev setups in this repo use WSL.
- Requires: WSL installed, docker desktop running.
#>

param(
  [string]$ApiHost = "127.0.0.1",
  [int]$Port = 30002,
  [string]$Query = "quantum",
  [int]$Limit = 5,
  [int]$CandidateLimit = 200,
  [string]$DatabaseUrl = "postgresql://wordloom:wordloom@localhost:5435/wordloom_dev",
  [string]$ElasticUrl = "http://localhost:9200",
  [string]$ElasticIndex = "wordloom-search-index",
  [switch]$RecreateIndex,
  [switch]$KeepRunning
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Convert-ToWslPath([string]$WindowsPath) {
  $p = (Resolve-Path $WindowsPath).Path
  $drive = $p.Substring(0,1).ToLower()
  $rest = $p.Substring(2) -replace '\\','/'
  return "/mnt/$drive$rest"
}

function Quote-ForBash([string]$s) {
  # Wrap in single-quotes for bash, escaping any embedded single-quote.
  # bash pattern: 'foo'\''bar'
  return "'" + ($s -replace "'", "'\\''") + "'"
}

function Ensure-Elasticsearch() {
  $name = "wordloom-es"
  $running = docker ps --format "{{.Names}}" | Select-String -SimpleMatch $name
  if (-not $running) {
    $exists = docker ps -a --format "{{.Names}}" | Select-String -SimpleMatch $name
    if ($exists) {
      Write-Host "[smoke] Starting existing Elasticsearch container: $name" -ForegroundColor Cyan
      docker start $name | Out-Null
    } else {
      Write-Host "[smoke] Starting Elasticsearch container: $name" -ForegroundColor Cyan
      docker run -d --name $name -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.12.2 | Out-Null
    }
  }

  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline) {
    try {
      $null = Invoke-WebRequest -Uri "$ElasticUrl" -Method Get -TimeoutSec 2
      Write-Host "[smoke] Elasticsearch is reachable at $ElasticUrl" -ForegroundColor Green
      return
    } catch {
      Start-Sleep -Seconds 1
    }
  }

  throw "Elasticsearch not reachable at $ElasticUrl"
}

function Wait-ForHealth() {
  $healthPaths = @()
  $healthPaths += "http://$ApiHost`:$Port/api/v1/health"

  # Some environments don't forward WSL ports to Windows localhost reliably.
  # Try the WSL VM IP as a fallback.
  try {
    $wslIp = (wsl.exe -e bash -lc "hostname -I | awk '{print $1}'" 2>$null).Trim()
    if ($wslIp) {
      $healthPaths += "http://$wslIp`:$Port/api/v1/health"
    }
  } catch {
    # ignore
  }

  $deadline = (Get-Date).AddSeconds(120)
  while ((Get-Date) -lt $deadline) {
    foreach ($healthUrl in $healthPaths) {
      try {
        $res = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 2
        if ($res.StatusCode -eq 200) {
          Write-Host "[smoke] Health OK: $healthUrl" -ForegroundColor Green
          return ($healthUrl -replace '/api/v1/health$','')
        }
      } catch {
        # keep trying
      }
    }
    Start-Sleep -Milliseconds 800
  }
  throw "Backend health did not become ready. Tried: $($healthPaths -join ', ')"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$backendDir = Resolve-Path (Join-Path $repoRoot 'backend')
$wslBackendDir = Convert-ToWslPath $backendDir

Write-Host "[smoke] repoRoot=$repoRoot" -ForegroundColor DarkGray
Write-Host "[smoke] wslBackendDir=$wslBackendDir" -ForegroundColor DarkGray

Ensure-Elasticsearch

# Backfill ES from Postgres.
Write-Host "[smoke] Backfilling Elasticsearch from Postgres search_index" -ForegroundColor Cyan
$env:DATABASE_URL = $DatabaseUrl
$env:ELASTIC_URL = $ElasticUrl
$env:ELASTIC_INDEX = $ElasticIndex

$recreateArg = if ($RecreateIndex) { "--recreate" } else { "" }
python (Join-Path $backendDir 'scripts\backfill_elastic_search_index.py') $recreateArg --batch-size 500

# Start backend in WSL with Elastic Stage1.
Write-Host "[smoke] Starting uvicorn in WSL on ${ApiHost}:$Port" -ForegroundColor Cyan

$pidFile = "uvicorn_smoke_$Port.pid"
$logFile = "server_smoke_$Port.log"

$wslStartScript = "scripts/_smoke_start_uvicorn_wsl.sh"

$startCmd = @(
  'cd ', $wslBackendDir, '; ',
  'PORT=', $Port, ' ',
  'DATABASE_URL=', (Quote-ForBash $DatabaseUrl), ' ',
  'SEARCH_STAGE1_PROVIDER=', (Quote-ForBash 'elastic'), ' ',
  'ELASTIC_URL=', (Quote-ForBash $ElasticUrl), ' ',
  'ELASTIC_INDEX=', (Quote-ForBash $ElasticIndex), ' ',
  'PID_FILE=', (Quote-ForBash $pidFile), ' ',
  'LOG_FILE=', (Quote-ForBash $logFile), ' ',
  'bash ', $wslStartScript
) -join ''

$startOut = wsl.exe -e bash -lc $startCmd
if ($LASTEXITCODE -ne 0) {
  Write-Host "[smoke] Failed to start uvicorn in WSL (exit=$LASTEXITCODE). Output:" -ForegroundColor Red
  Write-Host $startOut
  $diagCmd = @(
    'cd "', $wslBackendDir, '"; ',
    ('echo "--- tail log ---"; tail -n 200 "' + $logFile + '" 2>/dev/null || true; '),
    "echo '--- ps ---'; ps -ef | grep -E 'uvicorn api\\.app\\.main:app' | grep -v grep || true; ",
    "echo '--- port ---'; (command -v ss >/dev/null 2>&1 && ss -lntp | grep ':$Port' || true)"
  ) -join ''
  wsl.exe -e bash -lc $diagCmd
  throw "uvicorn failed to start in WSL"
}

$baseUrl = Wait-ForHealth

# Call endpoint
$endpoint = "$baseUrl/api/v1/search/blocks/two-stage?q=$([Uri]::EscapeDataString($Query))&limit=$Limit&candidate_limit=$CandidateLimit"
Write-Host "[smoke] Calling two-stage endpoint:" -ForegroundColor Cyan
Write-Host "  $endpoint" -ForegroundColor DarkGray

$response = curl.exe -s $endpoint
Write-Host "[smoke] Response:" -ForegroundColor Green
Write-Host $response

# Show log excerpt
Write-Host "[smoke] Log excerpt (Stage1 provider + Elastic recall + two-stage request):" -ForegroundColor Cyan
$grepPattern = "search\.stage1\.|two_stage|ERROR|Exception|Traceback"
$logCmd = @(
  'cd "', $wslBackendDir, '"; ',
  ('tail -n 250 "' + $logFile + '" | grep -E ' + (Quote-ForBash $grepPattern) + ' || true')
) -join ''
wsl.exe -e bash -lc $logCmd

Write-Host "[smoke] Last 120 lines of backend log (for debugging):" -ForegroundColor Cyan
$tailCmd = @('cd "', $wslBackendDir, '"; tail -n 120 "', $logFile, '" || true') -join ''
wsl.exe -e bash -lc $tailCmd

if (-not $KeepRunning) {
  Write-Host "[smoke] Stopping uvicorn (WSL)" -ForegroundColor Cyan
  $stopCmd = @(
    'cd "', $wslBackendDir, '"; ',
    ('if [ -f "' + $pidFile + '" ]; then kill $(cat "' + $pidFile + '") 2>/dev/null || true; rm -f "' + $pidFile + '"; fi')
  ) -join ''
  wsl.exe -e bash -lc $stopCmd | Out-Null
}
