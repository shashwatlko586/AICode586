# Access & Credentials Checklist

Use this when moving from **local mock mode** to **production on GCP**.

## Required for full production

| Access | Owner / How to obtain | Used for |
|--------|------------------------|----------|
| **GCP Project** + billing | Cloud console | Cloud Run, Vertex AI, Artifact Registry |
| **Vertex AI API** enabled | `gcloud services enable aiplatform.googleapis.com` | Gemini 2.0 Flash + embeddings |
| **Service account JSON** or Workload Identity | IAM → Service Accounts | Runtime auth (`GOOGLE_APPLICATION_CREDENTIALS` or attached SA on Cloud Run) |
| **IAM roles** on SA | Vertex AI User, Cloud Run, Secret Accessor | Model calls + secrets |

## Vector database (choose one)

| Option | Credentials | Notes |
|--------|-------------|-------|
| **Weaviate Cloud** or self-hosted | `WEAVIATE_URL`, `WEAVIATE_API_KEY` | Set `VECTOR_DB_PROVIDER=weaviate` |
| **Pinecone** | `PINECONE_API_KEY`, index name | Set `VECTOR_DB_PROVIDER=pinecone`; create index dim **768** for `text-embedding-004` |
| **Chroma** (dev only) | None | Default locally; not recommended for multi-instance Cloud Run |

## Optional but recommended

| Access | Purpose |
|--------|---------|
| **Langfuse** (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`) | Traces: RAG chunks, LLM I/O, tool calls |
| **Google Secret Manager** | Store Langfuse / Pinecone / Weaviate keys on Cloud Run |
| **Artifact Registry** | Docker images for Cloud Run |
| **Cloud Build** | CI/CD via `cloudbuild.yaml` |

## No account required

| Item | Notes |
|------|-------|
| **Google Trends** | Public; accessed via `pytrends` (respect rate limits) |
| **Capstone PDFs/txt** | Already in `../Resources/` |
| **Prompts** | Local `prompts/` folder (can be separate Git repo) |

## Local demo without GCP

Set in `.env`:

```
MOCK_LLM=true
MOCK_TRENDS=true
VECTOR_DB_PROVIDER=chroma
```

Then run ingestion + API — no cloud keys needed.

## What to send your admin

1. GCP project ID and region (e.g. `us-central1`)
2. Choice of vector DB (Weaviate vs Pinecone)
3. Whether Langfuse is required
4. Cloud Run service name and public vs internal ingress
