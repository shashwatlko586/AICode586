#!/usr/bin/env bash
# Build, push, and deploy Shashwat Capstone Retail to Cloud Run.
# Reads secrets and settings from .env in the project root.
#
# Usage:
#   export GCP_PROJECT_ID=bdc-trainings
#   bash deploy/deploy-cloudrun.sh          # normal deploy
#   bash deploy/deploy-cloudrun.sh --clean  # delete service/repo first, then deploy
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-bdc-trainings}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="shashwat-capstone-retail"
REPO="shashwat-capstone-retail"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE}:latest"
ENV_FILE="deploy/cloudrun-env.yaml"

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.example to .env and set PINECONE_API_KEY."
  exit 1
fi

if [[ "${1:-}" == "--clean" ]]; then
  echo "=== Clean: delete Cloud Run service and Artifact Registry repo ==="
  gcloud run services delete "$SERVICE" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  (service not found)"
  gcloud artifacts repositories delete "$REPO" \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  (repo not found)"
  echo ""
  echo "=== Recreate GCP resources ==="
  bash deploy/gcloud-setup.sh
fi

echo "=== Generate Cloud Run env file from .env ==="
python3 <<'PY'
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import dotenv_values
except ImportError:
    dotenv_values = None

ROOT = Path(".")
OUT = ROOT / "deploy" / "cloudrun-env.yaml"

KEYS = [
    "GCP_PROJECT_ID",
    "GOOGLE_CLOUD_PROJECT",
    "GCP_LOCATION",
    "MOCK_LLM",
    "MOCK_TRENDS",
    "VECTOR_DB_PROVIDER",
    "EMBEDDING_DIMENSION",
    "VERTEX_GEMINI_MODEL",
    "VERTEX_EMBEDDING_MODEL",
    "PINECONE_API_KEY",
    "PINECONE_INDEX_NAME",
    "PINECONE_ENVIRONMENT",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
]

DEFAULTS = {
    "GCP_PROJECT_ID": "bdc-trainings",
    "GOOGLE_CLOUD_PROJECT": "bdc-trainings",
    "GCP_LOCATION": "us-central1",
    "MOCK_LLM": "false",
    "MOCK_TRENDS": "false",
    "VECTOR_DB_PROVIDER": "pinecone",
    "EMBEDDING_DIMENSION": "768",
    "VERTEX_GEMINI_MODEL": "gemini-2.5-flash",
    "VERTEX_EMBEDDING_MODEL": "text-embedding-005",
    "PINECONE_INDEX_NAME": "retail-layout-rag",
    "PINECONE_ENVIRONMENT": "us-east-1",
    "LANGFUSE_HOST": "https://cloud.langfuse.com",
}

file_env: dict[str, str | None] = {}
env_path = ROOT / ".env"
if dotenv_values and env_path.exists():
    file_env = dotenv_values(env_path)

merged: dict[str, str] = {}
for key in KEYS:
    val = (
        (file_env.get(key) if file_env else None)
        or os.getenv(key)
        or DEFAULTS.get(key)
        or ""
    )
    val = str(val).strip().strip('"').strip("'")
    if val:
        merged[key] = val

if merged.get("VECTOR_DB_PROVIDER", "").lower() == "chroma":
    print("WARNING: .env had VECTOR_DB_PROVIDER=chroma — forcing pinecone for Cloud Run", file=sys.stderr)
    merged["VECTOR_DB_PROVIDER"] = "pinecone"

if "GOOGLE_CLOUD_PROJECT" not in merged and "GCP_PROJECT_ID" in merged:
    merged["GOOGLE_CLOUD_PROJECT"] = merged["GCP_PROJECT_ID"]

if not merged.get("PINECONE_API_KEY") or merged["PINECONE_API_KEY"] == "your-pinecone-api-key":
    print("ERROR: Set a real PINECONE_API_KEY in .env before deploying.", file=sys.stderr)
    sys.exit(1)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(f"{k}: {v!r}" for k, v in merged.items()) + "\n", encoding="utf-8")
print(f"Wrote {OUT} ({len(merged)} vars, VECTOR_DB_PROVIDER={merged.get('VECTOR_DB_PROVIDER')})")
PY

echo ""
echo "=== Build & push image ==="
echo "Service: $SERVICE"
echo "Image:   $IMAGE"
gcloud builds submit --tag "$IMAGE" --project="$PROJECT_ID" --timeout=1200

echo ""
echo "=== Deploy to Cloud Run ==="
gcloud run deploy "$SERVICE" \
  --image="$IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --project="$PROJECT_ID" \
  --env-vars-file="$ENV_FILE"

URL="$(gcloud run services describe "$SERVICE" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format='value(status.url)')"

echo ""
echo "=== Grant Vertex AI access to Cloud Run service account ==="
SA="$(gcloud run services describe "$SERVICE" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || true)"
if [[ -z "$SA" ]]; then
  PN="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  SA="${PN}-compute@developer.gserviceaccount.com"
fi
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA}" \
  --role="roles/aiplatform.user" \
  --quiet 2>/dev/null || echo "  (skipped — ask GCP admin to grant roles/aiplatform.user to $SA)"

gcloud run services add-iam-policy-binding "$SERVICE" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --quiet 2>/dev/null || echo "  (public access skipped — ask admin if needed)"

echo ""
echo "============================================"
echo "  Deployed!"
echo "  Service: $SERVICE"
echo "  URL:     $URL"
echo "  Health:  ${URL}/health"
echo "============================================"
echo ""
echo "Update .env:"
echo "  CLOUD_RUN_API_URL=$URL"
echo ""
echo "Verify Pinecone:"
echo "  curl -s ${URL}/health | python3 -m json.tool"
echo ""
echo "Expected: \"vector_db\": \"pinecone\", \"env_vector_db\": \"pinecone\""
