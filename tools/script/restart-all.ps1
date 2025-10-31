#requires -Version 5.1
Set-StrictMode -Version Latest
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\stop-all.ps1"
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\start-all.ps1"