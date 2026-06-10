# Running on a Virtual Machine (Linux)

Use this guide when the project runs on a **GCP Compute Engine VM**, lab VM, or any Linux server — not on your local Windows laptop.

## 1. Copy project to the VM

From your laptop (PowerShell or terminal), upload the folder:

```bash
# Option A — scp (replace USER and VM_IP)
scp -r "C_AgenticAI_PRJ" USER@VM_IP:~/

# Option B — if using gcloud
gcloud compute scp --recurse C_AgenticAI_PRJ INSTANCE_NAME:~ --zone=YOUR_ZONE
```

On the VM you should have:

```
~/C_AgenticAI_PRJ/
├── Resources/              ← capstone PDFs (required for RAG)
└── shashwat-capstone-retail/      ← application code
```

## 2. One-command setup (recommended)

SSH into the VM:

```bash
ssh USER@VM_IP
cd ~/C_AgenticAI_PRJ/shashwat-capstone-retail
chmod +x deploy/setup-vm.sh
./deploy/setup-vm.sh
```

This installs Python deps, creates `.env`, ingests documents, and runs a smoke test.

## 3. Start the app

**Two terminals:**

```bash
# Terminal 1 — API
cd ~/C_AgenticAI_PRJ/shashwat-capstone-retail
./start-api.sh

# Terminal 2 — Streamlit UI
cd ~/C_AgenticAI_PRJ/shashwat-capstone-retail
./start-ui.sh
```

**Or single terminal:**

```bash
./run-demo.sh
```

## 4. Open in browser

Replace `VM_IP` with the VM’s **external IP** (GCP Console → Compute Engine → VM instances).

| Service | URL |
|---------|-----|
| API docs | `http://VM_IP:8080/docs` |
| Health | `http://VM_IP:8080/health` |
| Streamlit UI | `http://VM_IP:8501` |

### GCP firewall

Create ingress rules (or use “Allow HTTP traffic” + custom ports):

```bash
gcloud compute firewall-rules create allow-shashwat-capstone-retail \
  --allow=tcp:8080,tcp:8501 \
  --source-ranges=0.0.0.0/0 \
  --description="Architect Copilot API + Streamlit"
```

On Ubuntu VM:

```bash
sudo ufw allow 8080/tcp
sudo ufw allow 8501/tcp
```

## 5. Test API from VM

```bash
curl -s http://localhost:8080/health | python3 -m json.tool

curl -s -X POST http://localhost:8080/generate_layout \
  -H "Content-Type: application/json" \
  -d '{"city":"Surat","store_name":"Blue Retail Surat","floor_area_sqm":120}' \
  | python3 -m json.tool | head -40
```

Layout PNG is saved under `shashwat-capstone-retail/outputs/`.

## 6. Using real GCP Vertex AI on the VM

1. Attach a service account to the VM with **Vertex AI User**, or download a key JSON.
2. Edit `.env`:

```env
MOCK_LLM=false
MOCK_TRENDS=false
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/home/USER/keys/sa.json
VECTOR_DB_PROVIDER=chroma
```

3. Re-ingest (embeddings will use Vertex):

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python scripts/ingest_documents.py
./start-api.sh
```

## 7. Run in background (optional)

```bash
nohup ./start-api.sh > logs/api.log 2>&1 &
nohup ./start-ui.sh > logs/ui.log 2>&1 &
mkdir -p logs
```

Stop:

```bash
pkill -f "uvicorn src.api.main"
pkill -f "streamlit run"
```

## 8. Docker alternative

```bash
cd ~/C_AgenticAI_PRJ/shashwat-capstone-retail
mkdir -p data/Resources
cp ../Resources/* data/Resources/

docker compose up --build
# API at http://VM_IP:8000
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Resources directory not found` | Ensure `../Resources` exists relative to `shashwat-capstone-retail` |
| `indexed_chunks: 0` | Run `python scripts/ingest_documents.py` |
| Browser can’t connect | Open firewall ports 8080 / 8501 |
| Streamlit can’t reach API | Set `CLOUD_RUN_API_URL=http://127.0.0.1:8080` in `.env` |
| Vertex 403 | Enable Vertex AI API; check VM service account IAM |
| Out of memory on ingest | Use `MOCK_LLM=true` for dev; ingest fewer/lighter docs first |

## Quick reference

```bash
cd ~/C_AgenticAI_PRJ/shashwat-capstone-retail
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python scripts/ingest_documents.py   # once
./start-api.sh                       # port 8080
./start-ui.sh                        # port 8501
```
