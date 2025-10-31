param(
    [string]$DbHost = "localhost",
    [int]$Port = 5432,
    [string]$User = "postgres",
    [string]$PgPassword = $env:PGPASSWORD,
    [string[]]$Databases = @("wordloompg", "wordloomorbit"),
    [string]$InputDir = (Join-Path $PSScriptRoot "..\\backups"),
    [string[]]$SqlFiles,
    [switch]$UsePgPass,
    [string]$PgPassFile,
    [switch]$UseEnv,
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\\..\\..\\.env")
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $InputDir)) {
    throw "Input directory not found: $InputDir"
}

# Helpers
$resolvePath = {
    param($p)
    if ([string]::IsNullOrWhiteSpace($p)) { return $null }
    try { return (Resolve-Path -LiteralPath $p).Path } catch { return $p }
}

function Parse-PgUrl {
    param([string]$url)
    $pattern = '^postgresql(?:\+\w+)?://(?<user>[^:]+):(?<pass>[^@]+)@(?<host>[^:/]+)(?::(?<port>\d+))?/(?<db>[^?]+)'
    $m = [regex]::Match($url, $pattern)
    if (-not $m.Success) { return $null }
    return [ordered]@{
        user = $m.Groups['user'].Value
        pass = $m.Groups['pass'].Value
        host = $m.Groups['host'].Value
        port = if ($m.Groups['port'].Success) { [int]$m.Groups['port'].Value } else { 5432 }
        db   = $m.Groups['db'].Value
    }
}

function Try-Load-EnvConnection {
    param([string]$envPath)
    if (-not (Test-Path $envPath)) { return $null }
    $lines = Get-Content -LiteralPath $envPath -Encoding utf8 | Where-Object { $_ -and -not $_.Trim().StartsWith('#') }
    $kv = @{}
    foreach ($ln in $lines) {
        if ($ln -match '^(?<k>[A-Za-z0-9_]+)=(?<v>.*)$') { $kv[$matches.k] = $matches.v }
    }
    $main = if ($kv.ContainsKey('DATABASE_URL')) { Parse-PgUrl $kv['DATABASE_URL'] } else { $null }
    $orbit = if ($kv.ContainsKey('ORBIT_DB_URL')) { Parse-PgUrl $kv['ORBIT_DB_URL'] } else { $null }
    return [ordered]@{ main = $main; orbit = $orbit }
}

# If requested, read connection from .env
if ($UseEnv) {
    $envPath = & $resolvePath $EnvFile
    $envConn = Try-Load-EnvConnection -envPath $envPath
    if ($envConn -and $envConn.main) {
        $DbHost = $envConn.main.host
        $Port   = $envConn.main.port
        $User   = $envConn.main.user
        if (-not $PgPassword) { $PgPassword = $envConn.main.pass }
    }
}

if (-not $PgPassword -and -not $UsePgPass) {
    Write-Warning "PGPASSWORD not set. If your local server requires a password, you'll be prompted now."
    try {
        $sec = Read-Host -Prompt "Enter local Postgres password for user '$User' (input hidden)" -AsSecureString
        if ($sec) {
            $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
            $PgPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    } catch {
        Write-Warning "No password entered; proceeding without PGPASSWORD."
    }
}

$tempPgPass = $null
if ($UsePgPass) {
    # Build a temporary pgpass file if not provided
    if (-not $PgPassFile) {
        $tempPgPass = Join-Path $env:TEMP ("pgpass_wordloom_{0}.conf" -f ([System.Guid]::NewGuid().ToString('N')))
        $PgPassFile = $tempPgPass
    }

    # Compose entries; one wildcard line is enough for both databases
    if (-not $PgPassword) {
        # If user didn't pass a password explicitly, prompt discreetly
        $sec = Read-Host -Prompt "Enter password for user '$User' to write pgpass (input hidden)" -AsSecureString
        if ($sec) {
            $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
            $PgPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }

    if (-not $PgPassword) { throw "Password is required to create pgpass entries." }

    $entry = "{0}:{1}:*:{2}:{3}" -f $DbHost, $Port, $User, $PgPassword
    $dir = Split-Path $PgPassFile -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -Path $PgPassFile -Value $entry -Encoding ascii -NoNewline
    $env:PGPASSFILE = $PgPassFile
}

foreach ($db in $Databases) {
    $latest = $null
    if ($SqlFiles -and $SqlFiles.Count -gt 0) {
        $byName = $SqlFiles | Where-Object { $_ -match ("${db}\.sql$") }
        $pick = if ($byName) { $byName[0] } else { $SqlFiles[0] }
        $latest = & $resolvePath $pick
    } else {
        $cand = Get-ChildItem -Path $InputDir -Filter ("{0}_*.sql" -f $db) -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($cand) { $latest = $cand.FullName }
    }

    if (-not $latest) {
        # Fallback to storage root: ..\..\{db}.sql
        $storageRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\.." )).Path
        $cand2 = Join-Path $storageRoot ("{0}.sql" -f $db)
        if (Test-Path $cand2) { $latest = $cand2 }
    }

    if (-not $latest) { Write-Warning "No dump file found for $db"; continue }

    Write-Host ("Importing {0} from {1}" -f $db, $latest) -ForegroundColor Cyan

    # Ensure database exists (ignore if already exists)
    try {
        & createdb -h $DbHost -p $Port -U $User $db 2>$null | Out-Null
    } catch {
        Write-Verbose "createdb returned a non-zero exit (possibly already exists). Proceeding..."
    }

    # Import
    if ($PgPassword -and -not $UsePgPass) { $env:PGPASSWORD = $PgPassword }
    & psql -h $DbHost -p $Port -U $User -d $db -f $latest
}

Write-Host "Import finished." -ForegroundColor Green

if ($tempPgPass -and (Test-Path $tempPgPass)) {
    try { Remove-Item $tempPgPass -Force } catch { }
}
