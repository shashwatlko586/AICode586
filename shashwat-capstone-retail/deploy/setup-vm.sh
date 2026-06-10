#!/usr/bin/env bash
# Shashwat Capstone Retail — one-shot setup for Linux VM (Ubuntu/Debian)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESOURCES_DEFAULT="$(cd "$PROJECT_ROOT/.." 2>/dev/null && pwd)/Resources"

echo "=== Shashwat Capstone Retail — VM Setup ==="
echo "Project: $PROJECT_ROOT"

# --- 1. System packages ---
if command -v apt-get &>/dev/null; then
  echo "[1/6] Installing system packages (apt)..."
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3 python3-pip python3-venv git curl
elif command -v yum &>/dev/null; then
  echo "[1/6] Installing system packages (yum)..."
  sudo yum install -y python3 python3-pip git curl
else
  echo "[1/6] Skipping package install — ensure python3 and pip are installed."
fi

# --- 2. Python venv ---
echo "[2/6] Creating virtual environment..."
cd "$PROJECT_ROOT"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# --- 3. Environment file ---
echo "[3/6] Configuring .env..."
if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# Resolve Resources path
if [[ -d "$RESOURCES_DEFAULT" ]]; then
  RESOURCES_DIR="$RESOURCES_DEFAULT"
elif [[ -d "$PROJECT_ROOT/data/Resources" ]]; then
  RESOURCES_DIR="$PROJECT_ROOT/data/Resources"
else
  echo "WARNING: Resources folder not found."
  echo "  Expected: $RESOURCES_DEFAULT"
  echo "  Copy capstone PDFs/txt into ../Resources or shashwat-capstone-retail/data/Resources"
  RESOURCES_DIR="$RESOURCES_DEFAULT"
fi

# Append VM-friendly defaults if not already set
grep -q "^MOCK_LLM=" .env 2>/dev/null || echo "MOCK_LLM=true" >> .env
grep -q "^MOCK_TRENDS=" .env 2>/dev/null || echo "MOCK_TRENDS=true" >> .env
grep -q "^VECTOR_DB_PROVIDER=" .env 2>/dev/null || echo "VECTOR_DB_PROVIDER=pinecone" >> .env
sed -i.bak "s|^RESOURCES_DIR=.*|RESOURCES_DIR=$RESOURCES_DIR|" .env 2>/dev/null || echo "RESOURCES_DIR=$RESOURCES_DIR" >> .env

export PYTHONPATH="$PROJECT_ROOT"
export RESOURCES_DIR
export MOCK_LLM="${MOCK_LLM:-true}"
export MOCK_TRENDS="${MOCK_TRENDS:-true}"
export VECTOR_DB_PROVIDER="${VECTOR_DB_PROVIDER:-pinecone}"

# --- 4. Ingest documents ---
echo "[4/6] Ingesting RAG documents from: $RESOURCES_DIR"
if [[ -d "$RESOURCES_DIR" ]] && [[ "$(ls -A "$RESOURCES_DIR" 2>/dev/null)" ]]; then
  python scripts/ingest_documents.py
else
  echo "SKIP ingest — Resources folder empty or missing."
fi

# --- 5. Helper scripts ---
echo "[5/6] Creating start/stop scripts..."
cat > "$PROJECT_ROOT/start-api.sh" << 'EOF'
#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
set -a && source .env && set +a
export PYTHONPATH="$(pwd)"
echo "API: http://0.0.0.0:${API_PORT:-8080}"
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${API_PORT:-8080}"
EOF

cat > "$PROJECT_ROOT/start-ui.sh" << 'EOF'
#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
set -a && source .env && set +a
export CLOUD_RUN_API_URL="${CLOUD_RUN_API_URL:-http://127.0.0.1:8080}"
echo "Streamlit UI: http://0.0.0.0:8501"
echo "API target: $CLOUD_RUN_API_URL"
exec streamlit run streamlit_app/app.py --server.address 0.0.0.0 --server.port 8501
EOF

cat > "$PROJECT_ROOT/run-demo.sh" << 'EOF'
#!/usr/bin/env bash
# Start API in background, then UI in foreground
cd "$(dirname "$0")"
./start-api.sh &
API_PID=$!
sleep 3
echo "API PID: $API_PID"
trap "kill $API_PID 2>/dev/null" EXIT
./start-ui.sh
EOF

chmod +x "$PROJECT_ROOT/start-api.sh" "$PROJECT_ROOT/start-ui.sh" "$PROJECT_ROOT/run-demo.sh"

# --- 6. Quick health test ---
echo "[6/6] Smoke test..."
python -c "
from src.agents.graph import run_copilot
r = run_copilot(city='Surat', store_name='Blue Retail Surat', floor_area_sqm=120)
assert r.get('layout_plan_json'), 'No layout plan'
assert r.get('layout_image_path'), 'No image'
print('OK — layout generated:', r['layout_image_path'])
"

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "  Terminal 1:  ./start-api.sh"
echo "  Terminal 2:  ./start-ui.sh"
echo "  Or one shot: ./run-demo.sh"
echo ""
echo "  From your laptop (replace VM_IP):"
echo "    API:  http://VM_IP:8080/docs"
echo "    UI:   http://VM_IP:8501"
echo ""
echo "  Open VM firewall if needed:"
echo "    sudo ufw allow 8080/tcp"
echo "    sudo ufw allow 8501/tcp"
echo ""
echo "  For GCP Vertex AI (production), edit .env:"
echo "    MOCK_LLM=false, GCP_PROJECT_ID=..., GOOGLE_APPLICATION_CREDENTIALS=..."
echo "============================================"