param(
    [string]$Container = "wordloompg",
    [string[]]$Databases = @("wordloompg", "wordloomorbit"),
    [string]$User = "postgres",
    [string]$OutputDir = (Join-Path $PSScriptRoot "..\backups")
)

$ErrorActionPreference = "Stop"

# Ensure output directory exists
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$ts = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "Exporting from container '$Container' as user '$User'..." -ForegroundColor Cyan

foreach ($db in $Databases) {
    $file = Join-Path $OutputDir ("{0}_{1}.sql" -f $db, $ts)
    Write-Host ("  - Dumping database {0} -> {1}" -f $db, $file)

    # Capture STDOUT and save as UTF8 without BOM
    $dump = & docker exec $Container pg_dump -U $User -d $db --no-owner --no-privileges
    $dump | Set-Content -Path $file -NoNewline -Encoding utf8
}

Write-Host "Done. Dumps saved in: $OutputDir" -ForegroundColor Green
