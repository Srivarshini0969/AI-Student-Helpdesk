$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
Write-Host "Setup finished. Pull Ollama models, add college documents, then run .\run.ps1" -ForegroundColor Green
