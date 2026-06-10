# Deployment Manual
## Shashwat Capstone Retail — GCP Cloud Run

**Version:** 1.0  
**Target platform:** Google Cloud Platform  
**Primary region:** `us-central1`  
**Example project:** `bdc-trainings`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Architecture (Deployment View)](#3-architecture-deployment-view)
4. [Initial Setup](#4-initial-setup)
5. [Configure Environment](#5-configure-environment)
6. [Ingest RAG Documents](#6-ingest-rag-documents)
7. [Deploy to Cloud Run](#7-deploy-to-cloud-run)
8. [Run Streamlit UI](#8-run-streamlit-ui)
9. [Verify Deployment](#9-verify-deployment)
10. [Update & Redeploy](#10-update--redeploy)
11. [Troubleshooting](#11-troubleshooting)
12. [Appendix: Environment Variables](#12-appendix-environment-variables)

---

## 1. Overview

This manual describes how to deploy the **Architect Copilot API** to **Google Cloud Run** with:

- **Vertex AI** (Gemini 2.5 Flash + text-embedding-005)
- **Pinecone** (production vector database)
- **Artifact Registry** (Docker images)
- **Cloud Build** (container build)

The Streamlit UI runs separately on a VM or workstation and calls the Cloud Run API.

---

## 2. Prerequisites

### 2.1 Accounts & Access

| Requirement | Details |
|-------------|---------|
| GCP project | Billing enabled (e.g. `bdc-trainings`) |
| gcloud CLI | Installed and authenticated |
| Pinecone account | API key + serverless index (768 dimensions) |
| VM / workstation | Linux recommended for deploy scripts |

### 2.2 Authenticate GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project bdc-trainings
```

### 2.3 IAM Roles Required

**Your user account** (or admin) needs permission to deploy.  
**Cloud Run runtime service account** needs:

| Role | Purpose |
|------|---------|
| `roles/aiplatform.user` | Call Vertex AI Gemini + embeddings |
| `roles/run.invoker` | Invoke Cloud Run (if using authenticated access) |

**Cloud Build service accounts** need (for `gcloud builds submit`):

| Role | Purpose |
|------|---------|
| `roles/artifactregistry.writer` | Push Docker images |
| `roles/run.admin` | Deploy Cloud Run |
| `roles/storage.admin` | Cloud Build staging |
| `roles/logging.logWriter` | Build logs |

Default service accounts:

```
456822750436@cloudbuild.gserviceaccount.com
456822750436-compute@developer.gserviceaccount.com
```

> If IAM commands fail with `setIamPolicy denied`, ask your lab administrator to grant the roles above.

### 2.4 Software on VM

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl
```

---

## 3. Architecture (Deployment View)

```
┌──────────────┐     HTTPS      ┌─────────────────────────────────┐
│  Streamlit   │ ─────────────► │  Cloud Run                      │
│  (VM :8501)  │                │  shashwat-capstone-retail       │
└──────────────┘                │  FastAPI + LangGraph pipeline   │
                                └──────────┬──────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
             ┌────────────┐        ┌────────────┐        ┌────────────┐
             │ Vertex AI  │        │  Pinecone  │        │ Google     │
             │ Gemini +   │        │  Index     │        │ Trends     │
             │ Embeddings │        │  (768-dim) │        │ (pytrends) │
             └────────────┘        └────────────┘        └────────────┘

Build path:
  Source → Cloud Build → Artifact Registry → Cloud Run
```

---

## 4. Initial Setup

### 4.1 Clone / Copy Project

```bash
cd ~/Desktop/C_AgenticAI_PRJ11/shashwat-capstone-retail
```

Expected layout:

```
C_AgenticAI_PRJ11/
├── Resources/                    # RAG documents
└── shashwat-capstone-retail/     # Application (open this in VS Code)
```

### 4.2 Python Virtual Environment

```bash
cd ~/Desktop/C_AgenticAI_PRJ11/shashwat-capstone-retail
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export PYTHONPATH=$(pwd)
```

Or run the automated setup:

```bash
chmod +x deploy/setup-vm.sh
./deploy/setup-vm.sh
```

### 4.3 Enable GCP Services & Create Artifact Registry

```bash
export GCP_PROJECT_ID=bdc-trainings
export GCP_REGION=us-central1
bash deploy/gcloud-setup.sh
```

This enables:

- Vertex AI API  
- Cloud Run API  
- Artifact Registry  
- Cloud Build  
- Secret Manager  

And creates Docker repo: `shashwat-capstone-retail`

---

## 5. Configure Environment

### 5.1 Create `.env`

```bash
cp .env.example .env
nano .env
```

### 5.2 Required `.env` Values (Production)

```env
GCP_PROJECT_ID=bdc-trainings
GOOGLE_CLOUD_PROJECT=bdc-trainings
GCP_LOCATION=us-central1

MOCK_LLM=false
MOCK_TRENDS=false

VECTOR_DB_PROVIDER=pinecone
EMBEDDING_DIMENSION=768
PINECONE_API_KEY=<your-pinecone-api-key>
PINECONE_INDEX_NAME=retail-layout-rag
PINECONE_ENVIRONMENT=us-east-1

VERTEX_GEMINI_MODEL=gemini-2.5-flash
VERTEX_EMBEDDING_MODEL=text-embedding-005

LANGFUSE_ENABLED=false

RESOURCES_DIR=../Resources
CLOUD_RUN_API_URL=http://localhost:8080
```

### 5.3 Critical Checks

```bash
# Must show pinecone — NOT chroma
grep VECTOR_DB .env

# Must NOT list chroma anywhere
grep -i chroma .env

# Real Pinecone key (not placeholder)
grep PINECONE_API_KEY .env
```

### 5.4 Pinecone Index Setup

In [Pinecone Console](https://app.pinecone.io):

| Setting | Value |
|---------|-------|
| Index name | `retail-layout-rag` |
| Dimensions | **768** |
| Metric | cosine |
| Type | Serverless |
| Region | `us-east-1` (AWS) |

---

## 6. Ingest RAG Documents

Run **once** on the VM (embeds into Pinecone via Vertex AI):

```bash
cd ~/Desktop/C_AgenticAI_PRJ11/shashwat-capstone-retail
source .venv/bin/activate
export PYTHONPATH=$(pwd)
set -a && source .env && set +a

python scripts/ingest_documents.py
```

Expected output:

```
Upserted N chunks …
```

Documents are read from `../Resources/`:

- `National_Building_Code_Accessibility_Chapter.txt`
- `Retail_Design_Best_Practices.md.txt`
- (Add PDFs when available: Brand Book, Fixture Catalog, Leasing Agreement)

### Optional: Copy resources into Docker context

```bash
mkdir -p data/Resources
cp ../Resources/* data/Resources/
```

---

## 7. Deploy to Cloud Run

### 7.1 Standard Deploy (Recommended)

```bash
cd ~/Desktop/C_AgenticAI_PRJ11/shashwat-capstone-retail
export GCP_PROJECT_ID=bdc-trainings
chmod +x deploy/*.sh
bash deploy/deploy-cloudrun.sh
```

The script:

1. Reads `.env` and writes `deploy/cloudrun-env.yaml`  
2. Builds Docker image via Cloud Build  
3. Pushes to Artifact Registry  
4. Deploys to Cloud Run with env vars file  
5. Attempts Vertex AI IAM grant and public access  

### 7.2 Clean Redeploy (Delete & Recreate)

```bash
bash deploy/deploy-cloudrun.sh --clean
```

### 7.3 Env-Only Update (No Rebuild)

Use when only environment variables change:

```bash
bash deploy/deploy-cloudrun.sh --env-only
```

> **Note:** Dependency changes (`requirements.txt`) require a **full redeploy**, not `--env-only`.

### 7.4 Manual Deploy (Alternative)

```bash
export GCP_PROJECT_ID=bdc-trainings
export GCP_REGION=us-central1
IMAGE=us-central1-docker.pkg.dev/bdc-trainings/shashwat-capstone-retail/shashwat-capstone-retail:latest

gcloud builds submit --tag "$IMAGE" --project=bdc-trainings --timeout=1200

gcloud run deploy shashwat-capstone-retail \
  --image="$IMAGE" \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --project=bdc-trainings \
  --env-vars-file=deploy/cloudrun-env.yaml
```

Generate `cloudrun-env.yaml` first by running the deploy script (it creates the file before build).

### 7.5 Cloud Build YAML (Alternative)

```bash
gcloud builds submit --config=cloudbuild.yaml --project=bdc-trainings
```

> Prefer `deploy/deploy-cloudrun.sh` — it includes Pinecone secrets from `.env`.

---

## 8. Run Streamlit UI

After deploy, copy the Cloud Run URL from script output:

```bash
# Update .env
CLOUD_RUN_API_URL=https://shashwat-capstone-retail-XXXXX-uc.a.run.app
```

Start UI:

```bash
source .venv/bin/activate
set -a && source .env && set +a
./start-ui.sh
```

Open in browser: `http://<VM-IP>:8501`

### Firewall (if needed)

```bash
sudo ufw allow 8501/tcp
```

---

## 9. Verify Deployment

### 9.1 Health Check

```bash
curl -s https://YOUR-CLOUD-RUN-URL/health | python3 -m json.tool
```

Expected:

```json
{
  "status": "ok",
  "vector_db": "pinecone",
  "indexed_chunks": -1,
  "mock_llm": false,
  "mock_trends": false
}
```

(`indexed_chunks: -1` is normal for Pinecone.)

### 9.2 Generate Layout Test

```bash
curl -s -X POST https://YOUR-CLOUD-RUN-URL/generate_layout \
  -H "Content-Type: application/json" \
  -d '{"city":"Surat","store_name":"Blue Retail Surat","floor_area_sqm":120}' \
  | python3 -m json.tool | head -30
```

### 9.3 Confirm Cloud Run Environment

```bash
gcloud run services describe shashwat-capstone-retail \
  --region=us-central1 \
  --project=bdc-trainings \
  --format="yaml(spec.template.spec.containers[0].env)" | grep -A1 VECTOR
```

---

## 10. Update & Redeploy

| Change type | Command |
|-------------|---------|
| Code change | `bash deploy/deploy-cloudrun.sh` |
| `.env` only | `bash deploy/deploy-cloudrun.sh --env-only` |
| New Python package | Full redeploy (rebuilds Docker image) |
| Re-ingest RAG | `python scripts/ingest_documents.py` (no redeploy needed) |

---

## 11. Troubleshooting

### `vector_db: chroma` on /health

**Cause:** Cloud Run missing `VECTOR_DB_PROVIDER=pinecone`  
**Fix:**

```bash
bash deploy/deploy-cloudrun.sh --env-only
```

Ensure `.env` has no `VECTOR_DB_PROVIDER=chroma`.

---

### `404 Publisher Model … gemini-2.0-flash-001`

**Cause:** Retired Gemini model  
**Fix:**

```bash
gcloud run services update shashwat-capstone-retail \
  --region=us-central1 \
  --project=bdc-trainings \
  --update-env-vars=VERTEX_GEMINI_MODEL=gemini-2.5-flash,VERTEX_EMBEDDING_MODEL=text-embedding-005
```

---

### `'Langfuse' object has no attribute 'trace'`

**Cause:** Langfuse SDK v3 incompatibility  
**Fix:** Disable Langfuse on Cloud Run:

```bash
gcloud run services update shashwat-capstone-retail \
  --region=us-central1 \
  --project=bdc-trainings \
  --remove-env-vars=LANGFUSE_PUBLIC_KEY,LANGFUSE_SECRET_KEY,LANGFUSE_HOST \
  --update-env-vars=LANGFUSE_ENABLED=false
```

Then redeploy with updated `src/observability/langfuse_tracer.py`.

---

### Pinecone package rename error

**Cause:** Old `pinecone-client` in Docker image  
**Fix:** Update `requirements.txt` to `pinecone>=5.0.0`, then full redeploy:

```bash
pip uninstall -y pinecone-client
pip install "pinecone>=5.0.0"
bash deploy/deploy-cloudrun.sh
```

---

### `403 Permission denied` on Vertex AI

**Cause:** Cloud Run service account lacks Vertex access  
**Fix:** Admin grants `roles/aiplatform.user` to:

```
456822750436-compute@developer.gserviceaccount.com
```

Temporary workaround:

```bash
gcloud run services update shashwat-capstone-retail \
  --update-env-vars=MOCK_LLM=true,MOCK_TRENDS=true
```

---

### JSON parse / `Unterminated string` errors

**Cause:** Gemini returned malformed JSON  
**Fix:** Redeploy with updated `src/llm/vertex_client.py` and `src/agents/layout_strategist.py` (JSON mode + fallback layout).

---

### Cloud Build push denied

**Cause:** Missing Artifact Registry IAM  
**Fix:** Run `bash deploy/gcloud-setup.sh` or ask admin for `artifactregistry.writer` on Cloud Build SA.

---

### Empty RAG results

**Fix:**

```bash
python scripts/ingest_documents.py
curl -s $CLOUD_RUN_API_URL/health
```

---

## 12. Appendix: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GCP_PROJECT_ID` | Yes | — | GCP project for Vertex AI |
| `GOOGLE_CLOUD_PROJECT` | Yes | same as above | ADC project |
| `GCP_LOCATION` | Yes | `us-central1` | Vertex AI region |
| `VERTEX_GEMINI_MODEL` | Yes | `gemini-2.5-flash` | LLM model ID |
| `VERTEX_EMBEDDING_MODEL` | Yes | `text-embedding-005` | Embedding model |
| `EMBEDDING_DIMENSION` | Yes | `768` | Vector dimension |
| `VECTOR_DB_PROVIDER` | Yes | `pinecone` | `pinecone` / `chroma` / `weaviate` |
| `PINECONE_API_KEY` | Yes (prod) | — | Pinecone API key |
| `PINECONE_INDEX_NAME` | Yes | `retail-layout-rag` | Index name |
| `PINECONE_ENVIRONMENT` | Yes | `us-east-1` | Pinecone region |
| `MOCK_LLM` | No | `false` | Skip Vertex for LLM |
| `MOCK_TRENDS` | No | `false` | Skip live Google Trends |
| `LANGFUSE_ENABLED` | No | `false` | Enable Langfuse tracing |
| `LANGFUSE_PUBLIC_KEY` | If enabled | — | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | If enabled | — | Langfuse secret key |
| `RESOURCES_DIR` | Local | `../Resources` | RAG document path |
| `CLOUD_RUN_API_URL` | UI | — | API URL for Streamlit |

---

## Deploy Checklist

```
□ gcloud authenticated
□ GCP APIs enabled (gcloud-setup.sh)
□ .env configured (pinecone, gemini-2.5-flash)
□ Pinecone index created (768-dim)
□ Documents ingested (ingest_documents.py)
□ deploy-cloudrun.sh completed
□ /health shows vector_db: pinecone
□ /generate_layout returns layout JSON + image
□ Streamlit UI connected to Cloud Run URL
```

---

**Document references:**  
- [Technical Design Document](TECHNICAL_DESIGN.md)  
- [User Guide](USER_GUIDE.md)
