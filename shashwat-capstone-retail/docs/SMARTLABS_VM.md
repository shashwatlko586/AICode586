# SmartLabs VM + Visual Studio Code Setup

Guide for running Architect Copilot on your **SmartLabs Guacamole VM** using **VS Code**.

> **Security:** Never commit passwords or service-account JSON to Git. Use `.env` locally only (already in `.gitignore`).

---

## Part A — Connect to the VM

1. Log in at [SmartLabs Login](https://app.smartlabs.pro/login) with your lab credentials.
2. Open your VM session from the Guacamole client link provided by your instructor.
3. Inside the VM desktop, open **Visual Studio Code** (or install it):

```bash
sudo apt update
sudo apt install -y code  # or download from https://code.visualstudio.com/
```

4. Copy or clone the project into the VM, e.g.:

```bash
# If uploaded as zip
cd ~
unzip C_AgenticAI_PRJ.zip
# Expected:
# ~/C_AgenticAI_PRJ/Resources/
# ~/C_AgenticAI_PRJ/shashwat-capstone-retail/
```

5. In VS Code: **File → Open Folder** → select `shashwat-capstone-retail`.

---

## Part B — First-time setup (VS Code terminal)

Open terminal in VS Code: **Terminal → New Terminal**, then:

```bash
cd ~/C_AgenticAI_PRJ/shashwat-capstone-retail
chmod +x deploy/setup-vm.sh
./deploy/setup-vm.sh
```

Or use VS Code task: **Terminal → Run Task → Setup VM (first time)**.

This creates `.venv`, installs packages, ingests PDFs from `../Resources`, and runs a smoke test.

---

## Part C — Run from VS Code

### Option 1 — Debugger (recommended)

1. Open **Run and Debug** (Ctrl+Shift+D).
2. Select **API + Streamlit** and press F5.

Or run separately:
- **FastAPI: Architect Copilot** → http://localhost:8080/docs
- **Streamlit UI** → http://localhost:8501

### Option 2 — Tasks

**Terminal → Run Task →**
1. `Start API (port 8080)`
2. `Start Streamlit UI (port 8501)`

### Option 3 — Shell scripts

```bash
./start-api.sh    # terminal 1
./start-ui.sh     # terminal 2
```

---

## Part D — GCP / Vertex AI on SmartLabs VM

Your lab GCP account is used via **browser login**, not a password in `.env`.

### 1. Install gcloud (if missing)

```bash
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
tar -xf google-cloud-cli-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
source ~/.bashrc
```

### 2. Authenticate

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

Use your **GCP lab email** when the browser opens. Do **not** put the password in any file.

### 3. Enable APIs (once per project)

```bash
gcloud services enable aiplatform.googleapis.com
```

### 4. Update `.env`

```env
MOCK_LLM=false
MOCK_TRENDS=false
GCP_PROJECT_ID=your-lab-project-id
GCP_LOCATION=us-central1
VECTOR_DB_PROVIDER=chroma
RESOURCES_DIR=../Resources
```

Remove or comment out `GOOGLE_APPLICATION_CREDENTIALS` if using `gcloud auth application-default login`.

### 5. Re-ingest and run

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python scripts/ingest_documents.py
```

Then F5 with **API + Streamlit**.

---

## Part E — Verify it works

In VS Code terminal:

```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```

```bash
curl -s -X POST http://localhost:8080/generate_layout \
  -H "Content-Type: application/json" \
  -d '{"city":"Surat","store_name":"Blue Retail Surat","floor_area_sqm":120}' \
  | python3 -m json.tool | head -30
```

Check `outputs/` for the PNG layout diagram.

---

## Troubleshooting on Guacamole VM

| Issue | Solution |
|-------|----------|
| VS Code Python not found | Select interpreter: Ctrl+Shift+P → **Python: Select Interpreter** → `.venv/bin/python` |
| `ModuleNotFoundError: src` | Set `PYTHONPATH` to project root (launch.json already does this) |
| Port in use | `pkill -f uvicorn; pkill -f streamlit` |
| RAG empty | Run task **Ingest RAG Documents** |
| Vertex 403 | Run `gcloud auth application-default login` and check project ID |
| Guacamole clipboard | Use Guacamole sidebar to paste long commands |

---

## Recommended workflow

1. **Day 1:** `./deploy/setup-vm.sh` with `MOCK_LLM=true` — confirm UI + API work.
2. **Day 2:** `gcloud auth` + set real `GCP_PROJECT_ID`, re-ingest, set `MOCK_LLM=false`.
3. **Demo:** Open Streamlit, enter Surat / 120 sqm, click **Generate layout**.
