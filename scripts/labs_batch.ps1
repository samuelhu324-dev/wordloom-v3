param(
  [int]$Repeats = 4,
  [string[]]$Scenarios = @(
    "es_bulk_partial",
    "db_claim_contention",
    "stuck_reclaim",
    "duplicate_delivery",
    "projection_version"
  ),
  [string]$PythonPath = "D:/Project/wordloom-v3/.venv/Scripts/python.exe",
  [string]$BaseRunId = "",
  [int]$KeepLast = 50,
  [string]$ExportLookback = "10m",
  [int]$ExportLimit = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure redirections write UTF-8 (Windows PowerShell defaults to UTF-16LE).
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Add-Content:Encoding'] = 'utf8'
$PSDefaultParameterValues['Set-Content:Encoding'] = 'utf8'

if (-not $BaseRunId) {
  $BaseRunId = Get-Date -Format "yyyyMMddTHHmmss"
}

$logDir = Join-Path $PSScriptRoot "..\logs"
New-Item -ItemType Directory -Force $logDir | Out-Null

$logPath = Join-Path $logDir "labs_batch_$BaseRunId.txt"
$summaryPath = Join-Path $logDir "labs_batch_$BaseRunId.summary.json"

"BASE=$BaseRunId" | Out-File -FilePath $logPath

function Write-Log([string]$line) {
  Add-Content -Path $logPath -Value $line
  Write-Host $line
}

function Get-RunDir([string]$scenario, [string]$runId) {
  # Mirrors backend/scripts/cli.py default auto run dir.
  return Join-Path $PSScriptRoot "..\docs\labs\_snapshot\auto\S3A-2A-3A\$scenario\$runId"
}

function Get-TraceCount([string]$scenario, [string]$runId) {
  $runDir = Get-RunDir -scenario $scenario -runId $runId
  $exportsDir = Join-Path $runDir "_exports"
  if (-not (Test-Path $exportsDir)) { return 0 }
  $traceFile = Get-ChildItem -Path $exportsDir -Filter "jaeger-traces-tags-*.json" | Select-Object -First 1
  if (-not $traceFile) { return 0 }
  try {
    $obj = Get-Content $traceFile.FullName -Raw -Encoding utf8 | ConvertFrom-Json
    if ($null -eq $obj.data) { return 0 }
    return @($obj.data).Count
  } catch {
    return 0
  }
}

function Get-VerifyOk([string]$scenario, [string]$runId) {
  $runDir = Get-RunDir -scenario $scenario -runId $runId
  $resultPath = Join-Path $runDir "_result.json"
  if (-not (Test-Path $resultPath)) { return $false }
  $obj = Get-Content $resultPath -Raw -Encoding utf8 | ConvertFrom-Json
  if ($null -ne ($obj.PSObject.Properties.Name | Where-Object { $_ -eq 'ok' })) {
    return [bool]$obj.ok
  }

  if ($scenario -eq 'projection_version') {
    try {
      $v1 = $obj.probe.v1
      $v2 = $obj.probe.v2
      return [bool]($v1.found -and $v2.found -and ($v1.projection_version -eq 1) -and ($v2.projection_version -eq 2))
    } catch {
      return $false
    }
  }

  return $false
}

function Get-RunArgs([string]$scenario, [int]$i) {
  switch ($scenario) {
    "es_bulk_partial" {
      $port = 19120 + $i
      return @(
        '--metrics-port', "$port",
        '--duration', '20',
        '--trigger-count', '2',
        '--bulk-size', '10',
        '--partial-status', '400',
        '--scrape-delay', '1.0'
      )
    }
    "db_claim_contention" {
      $p1 = 19126 + (($i-1) * 2)
      $p2 = 19127 + (($i-1) * 2)
      return @(
        '--metrics-port-1', "$p1",
        '--metrics-port-2', "$p2",
        '--duration', '25',
        '--trigger-count', '8',
        '--batch-size', '1',
        '--poll-interval', '0.01',
        '--break-claim-sleep', '1.5',
        '--scrape-delay', '1.0'
      )
    }
    "stuck_reclaim" {
      $p1 = 19128 + (($i-1) * 2)
      $p2 = 19129 + (($i-1) * 2)
      return @(
        '--metrics-port-1', "$p1",
        '--metrics-port-2', "$p2",
        '--duration', '20',
        '--trigger-count', '5',
        '--lease-seconds', '3',
        '--reclaim-interval', '1.0',
        '--poll-interval', '0.1',
        '--batch-size', '50',
        '--claim-timeout', '8.0',
        '--scrape-delay', '1.5'
      )
    }
    "duplicate_delivery" {
      $port = 19130 + ($i-1)
      return @(
        '--metrics-port', "$port",
        '--duration', '20',
        '--delete-count', '2',
        '--scrape-delay', '1.0'
      )
    }
    "projection_version" {
      $port = 19110 + ($i-1)
      return @(
        '--metrics-port', "$port",
        '--duration', '10',
        '--projection-version-1', '1',
        '--projection-version-2', '2',
        '--poll-interval', '0.2',
        '--batch-size', '50',
        '--lease-seconds', '10',
        '--reclaim-interval', '2.0',
        '--scrape-delay', '1.0'
      )
    }
    default {
      throw "Unknown scenario: $scenario"
    }
  }
}

function Invoke-One([string]$scenario, [string]$runId, [string[]]$runArgs) {
  Write-Log "=== $scenario $runId ==="

  & $PythonPath backend/scripts/cli.py labs clean $scenario --keep-last $KeepLast *>> $logPath
  $rcClean1 = $LASTEXITCODE

  & $PythonPath backend/scripts/cli.py labs run $scenario --run-id $runId @runArgs *>> $logPath
  $rcRun = $LASTEXITCODE

  & $PythonPath backend/scripts/cli.py labs verify $scenario --run-id $runId *>> $logPath
  $rcVerify = $LASTEXITCODE

  & $PythonPath backend/scripts/cli.py labs export $scenario --run-id $runId --lookback $ExportLookback --limit $ExportLimit *>> $logPath
  $rcExport = $LASTEXITCODE

  & $PythonPath backend/scripts/cli.py labs clean $scenario --keep-last $KeepLast *>> $logPath
  $rcClean2 = $LASTEXITCODE

  Write-Log "rc(clean1,run,verify,export,clean2)=($rcClean1,$rcRun,$rcVerify,$rcExport,$rcClean2)"

  $ok = Get-VerifyOk -scenario $scenario -runId $runId
  $traces = Get-TraceCount -scenario $scenario -runId $runId

  return [pscustomobject]@{
    scenario = $scenario
    run_id = $runId
    verify_ok = $ok
    export_traces = $traces
    run_dir = (Get-RunDir -scenario $scenario -runId $runId)
    rc_run = $rcRun
    rc_verify = $rcVerify
    rc_export = $rcExport
  }
}

$results = @()
foreach ($scenario in $Scenarios) {
  for ($i = 1; $i -le $Repeats; $i++) {
    $runId = "$BaseRunId-$($scenario)-$i"
    $args = Get-RunArgs -scenario $scenario -i $i
    $res = Invoke-One -scenario $scenario -runId $runId -runArgs $args
    $results += $res

    if (-not $res.verify_ok -or $res.rc_run -ne 0 -or $res.rc_verify -ne 0) {
      Write-Log "FAILED: $($res.scenario) $($res.run_id)"
      $results | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryPath
      throw "Batch failed at $($res.scenario) $($res.run_id). See $logPath"
    }
  }
}

$results | ConvertTo-Json -Depth 5 | Out-File -FilePath $summaryPath
Write-Log "DONE. summary=$summaryPath"
