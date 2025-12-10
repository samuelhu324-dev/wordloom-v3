param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 30002
)

$ErrorActionPreference = "Stop"

$healthUrl = "http://$Host:$Port/api/v1/health"
Write-Host "Checking Wordloom API health at $healthUrl" -ForegroundColor Cyan

try {
  $res = Invoke-WebRequest -Uri $healthUrl -Method Get -TimeoutSec 8
  Write-Host "StatusCode:" $res.StatusCode -ForegroundColor Green
  Write-Host $res.Content
} catch {
  Write-Host "Health check failed:" $_.Exception.Message -ForegroundColor Red
  exit 1
}
