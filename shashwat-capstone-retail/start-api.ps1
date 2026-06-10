# Start Shashwat Capstone Retail on Windows (PowerShell)
$Root = $PSScriptRoot
Set-Location $Root

$Python = @(
    "$Root\.venv\Scripts\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") { $Python = $cmd.Source }
}

if (-not $Python) {
    Write-Host "Python not found. Install from https://www.python.org/downloads/ (check 'Add to PATH')"
    Write-Host "Or run: winget install Python.Python.3.11 --source winget"
    exit 1
}

Write-Host "Using Python: $Python"

if (-not (Test-Path "$Root\.venv")) {
    Write-Host "Creating virtual environment..."
    & $Python -m venv "$Root\.venv"
    & "$Root\.venv\Scripts\pip.exe" install -r "$Root\requirements.txt"
}

if (-not (Test-Path "$Root\.env")) {
    Copy-Item "$Root\.env.example" "$Root\.env"
}

$env:PYTHONPATH = $Root
$env:RESOURCES_DIR = Join-Path (Split-Path $Root -Parent) "Resources"
Get-Content "$Root\.env" | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}

Write-Host "Ingesting documents (first run may take 1-2 min)..."
& "$Root\.venv\Scripts\python.exe" "$Root\scripts\ingest_documents.py"

Write-Host ""
Write-Host "Starting API at http://localhost:8080"
Write-Host "Open another terminal and run: .\start-ui.ps1"
Write-Host ""
& "$Root\.venv\Scripts\python.exe" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8080
