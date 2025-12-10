# Restore wordloom databases from storage/*.sql using .env connection
param(
    [switch]$UsePgPass
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent  # .../storage/pg
$storage = Join-Path $root ".."          # .../storage
$pg = Join-Path $PSScriptRoot "import.ps1"

$files = @(
    (Join-Path $storage "wordloompg.sql"),
    (Join-Path $storage "wordloomorbit.sql")
) | Where-Object { Test-Path $_ }

if ($files.Count -eq 0) {
    throw "No storage SQL files found. Expected wordloompg.sql / wordloomorbit.sql under $storage"
}

$common = @('-UseEnv', '-SqlFiles', $files)
if ($UsePgPass) { $common += '-UsePgPass' }

& $pg @common
