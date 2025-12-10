#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 仓库根目录：tools\script 上两级
$Root   = (Resolve-Path "$PSScriptRoot\..\..").Path
$PgDir  = Join-Path $Root 'WordloomBackend\wordloompg'
$ApiDir = Join-Path $Root 'WordloomBackend\api'
$VenvDir= Join-Path $Root 'WordloomBackend\venv'
$FeDir  = Join-Path $Root 'WordloomFrontend\next'
$PidFile= Join-Path $PSScriptRoot '.pids.json'

function W($m){Write-Host "[*] $m" -f Cyan}
function OK($m){Write-Host "[✓] $m" -f Green}
function WW($m){Write-Host "[!] $m" -f Yellow}

function Start-DockerDesktop {
  W "Checking Docker Desktop..."
  $ok=$false; try{ docker info *> $null; $ok=$true }catch{}
  if(-not $ok){
    $exe="$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    if(-not (Test-Path $exe)){ $exe="$env:ProgramFiles(x86)\Docker\Docker\Docker Desktop.exe" }
    if(-not (Test-Path $exe)){ WW "Docker Desktop not found."; return $false }
    W "Starting Docker Desktop..."
    Start-Process -FilePath $exe | Out-Null
    $sw=[Diagnostics.Stopwatch]::StartNew()
    do{ Start-Sleep 3; try{ docker info *> $null; $ok=$true }catch{} }while(-not $ok -and $sw.Elapsed.TotalSeconds -lt 180)
    if(-not $ok){ WW "Docker not ready after 3 minutes."; return $false }
  }
  OK "Docker ready."; return $true
}

function Ensure-Venv {
  if(-not (Test-Path $VenvDir)){
    W "Creating python venv..."
    if(Get-Command py -Ea SilentlyContinue){ py -3 -m venv $VenvDir } else { python -m venv $VenvDir }
  }
  $py = Join-Path $VenvDir 'Scripts\python.exe'
  if(-not (Test-Path $py)){ throw "venv invalid: $VenvDir" }
  return $py
}

function Start-ComposePg {
  if(-not (Test-Path $PgDir)){ WW "PG compose dir missing: $PgDir"; return }
  Push-Location $PgDir
  try{
    if((Test-Path ".env.pg.example") -and -not (Test-Path ".env.pg")){ Copy-Item ".env.pg.example" ".env.pg"; W "Created .env.pg from example." }
    W "docker compose up -d (Postgres)..."
    docker compose --env-file .\.env.pg -f .\docker-compose.yml up -d
    OK "Postgres up."
  } finally { Pop-Location }
}

function Start-Backend {
  if(-not (Test-Path $ApiDir)){ throw "Backend dir not found: $ApiDir" }
  $py = Ensure-Venv
  $cmd = @"
cd "$ApiDir"
"$py" -m pip install -U pip
"$py" -m pip install -r requirements.txt
"$py" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --env-file .env
"@
  W "Starting backend (new window)..."
  $p = Start-Process powershell -ArgumentList "-NoExit","-Command",$cmd -WorkingDirectory $ApiDir -PassThru -WindowStyle Minimized
  OK "Backend PID: $($p.Id)"; return $p.Id
}

function Start-Frontend {
  if(-not (Test-Path $FeDir)){ throw "Frontend dir not found: $FeDir" }
  $cmd = @"
cd "$FeDir"
if (Get-Command pnpm -ErrorAction SilentlyContinue) { pnpm install; pnpm dev } else { npm install; npm run dev }
"@
  W "Starting frontend (new window)..."
  $p = Start-Process powershell -ArgumentList "-NoExit","-Command",$cmd -WorkingDirectory $FeDir -PassThru -WindowStyle Minimized
  OK "Frontend PID: $($p.Id)"; return $p.Id
}

if(-not (Start-DockerDesktop)){ exit 1 }
Start-ComposePg
$backendPid  = Start-Backend
$frontendPid = Start-Frontend

@{
  backendPid  = $backendPid
  frontendPid = $frontendPid
  time        = (Get-Date).ToString("s")
  apiDir      = $ApiDir
  feDir       = $FeDir
  pgDir       = $PgDir
} | ConvertTo-Json | Set-Content -Path $PidFile -Encoding UTF8
OK "PID file: $PidFile"

Start-Sleep 2
Start-Process "http://localhost:3000"
OK "All started."