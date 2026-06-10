$Root = $PSScriptRoot
Set-Location $Root

$env:PYTHONPATH = $Root
$env:CLOUD_RUN_API_URL = "http://127.0.0.1:8080"

Write-Host "Starting Streamlit at http://localhost:8501"
& "$Root\.venv\Scripts\python.exe" -m streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port 8501
