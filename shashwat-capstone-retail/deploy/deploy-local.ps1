# Local run (Windows PowerShell)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit before production."
}

$env:PYTHONPATH = $Root
$env:RESOURCES_DIR = Join-Path (Split-Path $Root -Parent) "Resources"
$env:MOCK_LLM = "true"
$env:MOCK_TRENDS = "true"
$env:VECTOR_DB_PROVIDER = "chroma"

Write-Host "Ingesting documents..."
python scripts/ingest_documents.py

Write-Host "Starting API on http://localhost:8080"
Start-Process python -ArgumentList "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080" -WorkingDirectory $Root

Write-Host "Run Streamlit in another terminal:"
Write-Host "  streamlit run streamlit_app/app.py"
