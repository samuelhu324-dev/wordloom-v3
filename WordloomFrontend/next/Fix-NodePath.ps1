<# 
  Fix-NodePath.ps1
  - Auto-detect Node.js/npm locations (incl. Chocolatey)
  - Add to System/User PATH if missing
  - Remove stray env var named "node"
  - Print summary and next steps
#>

# --- Helper: Read/Write PATH in Registry (System + User) ---
function Get-EnvPath {
  param([ValidateSet('Machine','User')]$Scope)
  if ($Scope -eq 'Machine') {
    (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" -Name Path -ErrorAction SilentlyContinue).Path
  } else {
    (Get-ItemProperty "HKCU:\Environment" -Name Path -ErrorAction SilentlyContinue).Path
  }
}

function Set-EnvPath {
  param([ValidateSet('Machine','User')]$Scope, [string]$NewPath)
  if ($Scope -eq 'Machine') {
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" -Name Path -Value $NewPath
  } else {
    Set-ItemProperty -Path "HKCU:\Environment" -Name Path -Value $NewPath
  }
}

function Add-ToPath {
  param([ValidateSet('Machine','User')]$Scope, [string[]]$Dirs)
  $original = Get-EnvPath -Scope $Scope
  if (-not $original) { $original = "" }
  $parts = $original -split ';' | Where-Object { $_ -and $_.Trim() -ne "" }
  $set = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  $parts | ForEach-Object { [void]$set.Add($_.TrimEnd('\')) }

  $added = @()
  foreach ($d in $Dirs) {
    $dir = $d.TrimEnd('\')
    if (Test-Path $dir) {
      if (-not $set.Contains($dir)) {
        $parts += $dir
        [void]$set.Add($dir)
        $added += $dir
      }
    }
  }

  $newPath = ($parts -join ';')
  if ($newPath -ne $original) {
    Set-EnvPath -Scope $Scope -NewPath $newPath
  }
  return $added
}

Write-Host ">>> Fix-NodePath.ps1 starting (requires Administrator)..." -ForegroundColor Cyan

# --- Candidate Node/npm directories ---
$candidates = @(
  "C:\Program Files\nodejs",                               # Official installer
  "C:\ProgramData\chocolatey\lib\nodejs\tools",            # choco nodejs
  "C:\ProgramData\chocolatey\lib\nodejs-lts\tools",        # choco nodejs-lts
  "C:\ProgramData\chocolatey\bin"                          # choco shim
) | Where-Object { Test-Path $_ }

if ($candidates.Count -eq 0) {
  Write-Warning "No Node.js directories found in common locations."
  Write-Host "Install via Chocolatey:" -ForegroundColor Yellow
  Write-Host "  choco install nodejs-lts -y" -ForegroundColor Yellow
} else {
  Write-Host "Found Node.js related directories:" -ForegroundColor Green
  $candidates | ForEach-Object { Write-Host "  $_" }
}

# --- Remove stray env var named 'node' (User + Machine) ---
foreach ($root in @("HKCU:\Environment","HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment")) {
  try {
    if (Get-ItemProperty -Path $root -Name "node" -ErrorAction SilentlyContinue) {
      Remove-ItemProperty -Path $root -Name "node" -ErrorAction SilentlyContinue
      Write-Host "Removed stray env var 'node' from $root" -ForegroundColor Yellow
    }
  } catch { }
}

# --- Add to PATHs ---
$addedUser   = Add-ToPath -Scope User    -Dirs $candidates
$addedSystem = Add-ToPath -Scope Machine -Dirs $candidates

if ($addedUser.Count -gt 0)   { Write-Host "Added to USER Path:"   -ForegroundColor Green; $addedUser   | ForEach-Object { Write-Host "  $_" } }
if ($addedSystem.Count -gt 0) { Write-Host "Added to SYSTEM Path:" -ForegroundColor Green; $addedSystem | ForEach-Object { Write-Host "  $_" } }

# --- Print final hints ---
Write-Host "`n>>> Done. Open a NEW PowerShell window and run:" -ForegroundColor Cyan
Write-Host "    node -v"
Write-Host "    npm -v"
Write-Host "`nIf versions show up, PATH is fixed. Then in your project run:" -ForegroundColor Cyan
Write-Host "    cd D:\Project\Wordloom\WordloomFrontend\next"
Write-Host "    npm install next@14 react react-dom typescript @types/node axios @tanstack/react-query zod clsx"
