#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
set -a && source .env && set +a
export PYTHONPATH="$(pwd)"
echo "API: http://0.0.0.0:${API_PORT:-8080}"
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${API_PORT:-8080}"
