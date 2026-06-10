#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
set -a && source .env && set +a
export CLOUD_RUN_API_URL="${CLOUD_RUN_API_URL:-http://127.0.0.1:8080}"
echo "Streamlit UI: http://0.0.0.0:8501"
echo "API target: $CLOUD_RUN_API_URL"
exec streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port 8501
