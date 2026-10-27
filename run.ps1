$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) { Write-Host "Run .\setup.ps1 first"; exit 1 }
& ".\.venv\Scripts\Activate.ps1"
python -m app.main
