#!/usr/bin/env bash
# One-time GCP setup for Shashwat Capstone Retail (run before first deploy)
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-bdc-trainings}"
REGION="${GCP_REGION:-us-central1}"
REPO="shashwat-capstone-retail"
SERVICE="shashwat-capstone-retail"

echo "Enabling APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project="$PROJECT_ID"

echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --project="$PROJECT_ID" 2>/dev/null || echo "  (repo already exists)"

gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo ""
echo "=== Cloud Build IAM (needed for gcloud builds submit) ==="
PN="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SAS=(
  "${PN}@cloudbuild.gserviceaccount.com"
  "${PN}-compute@developer.gserviceaccount.com"
)
ROLES=(
  roles/artifactregistry.writer
  roles/run.admin
  roles/iam.serviceAccountUser
  roles/logging.logWriter
  roles/storage.admin
)

for SA in "${SAS[@]}"; do
  echo "Granting roles to $SA ..."
  for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:${SA}" \
      --role="$ROLE" \
      --quiet 2>/dev/null || echo "  (skipped $ROLE — ask GCP admin)"
  done
done

echo ""
echo "=== Done ==="
echo "Next steps:"
echo "  1. Edit .env (PINECONE_API_KEY, LANGFUSE keys, MOCK_LLM=false)"
echo "  2. python scripts/ingest_documents.py"
echo "  3. bash deploy/deploy-cloudrun.sh"