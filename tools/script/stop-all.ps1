#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$Root   = (Resolve-Path "$PSScriptRoot\..\..").Path
$PidFile= Join-Path $PSScriptRoot '.pids.json'

function W($m){Write-Host "[*] $m" -f Cyan}
function OK($m){Write-Host "[✓] $m" -f Green}
function WW($m){Write-Host "[!] $m" -f Yellow}

if(Test-Path $PidFile){
  $meta = Get-Content $PidFile | ConvertFrom-Json
  foreach($pid in @($meta.backendPid,$meta.frontendPid)){
    if($pid){
      try{ $p=Get-Process -Id $pid -ErrorAction Stop; W "Stopping $pid ($($p.ProcessName))"; Stop-Process -Id $pid -Force }catch{}
    }
  }
  if($meta.pgDir -and (Test-Path $meta.pgDir)){
    Push-Location $meta.pgDir
    try{ W "docker compose down (Postgres)"; docker compose -f .\docker-compose.yml down; OK "Postgres stopped." }catch{ WW "compose down failed: $($_.Exception.Message)" } finally{ Pop-Location }
  }
  Remove-Item $PidFile -Force
  OK "Stopped all."
}else{
  WW "PID file not found, try default PG location."
  $pg = Join-Path $Root 'WordloomBackend\wordloompg'
  if(Test-Path $pg){ Push-Location $pg; try{ docker compose -f .\docker-compose.yml down }catch{}; Pop-Location }
}