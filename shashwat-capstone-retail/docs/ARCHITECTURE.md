# Technical Design — Architect Copilot

## 1. Overview

The system automates **conceptual retail layout** generation for Blue Retail Ventures expansion into Tier-2 cities (e.g. Surat). Design time is reduced from weeks to minutes while grounding outputs in official documents and live market signals.

## 2. Components

### 2.1 Orchestration (LangGraph)

- **State:** `CopilotState` carries city, trends, RAG chunks, JSON plan, image path, trace ID.
- **Flow:** `market_analyst` → `layout_strategist` → `draftsman` → END.

### 2.2 Market Analyst

- Tool: `pytrends` (`TrendReq`) with `geo=IN`, `sub_geo=IN-GJ` for Gujarat/Surat proxy.
- Outputs ranked keywords and LLM narrative for the strategist.
- `MOCK_TRENDS=true` for offline demos.

### 2.3 Layout Strategist

- **Retrieval:** Hybrid queries (layout + leasing + NBC + brand).
- **Generation:** Vertex AI Gemini 2.0 Flash with prompt from `prompts/layout_strategist_v1.txt`.
- **Validation:** Pydantic `LayoutPlan` schema.

### 2.4 AI Draftsman

- Deterministic Python + Matplotlib (not LLM): zones as colored rectangles, fixtures labeled with catalog IDs.

### 2.5 Vector database

| Provider | Use case |
|----------|----------|
| `chroma` | Local dev (default) |
| `weaviate` | Docker / Weaviate Cloud |
| `pinecone` | Managed serverless index |

Embeddings: Vertex `text-embedding-004` (mock hash vectors if `MOCK_LLM=true`).

### 2.6 Observability

- **Langfuse:** trace per `/generate_layout`, spans for RAG, strategist, draftsman.
- Alternative: MLflow (not wired; swap SDK in `src/observability/`).

### 2.7 Prompt management

- Prompts in `prompts/` — intended as a **dedicated Git repository** cloned at deploy time (`PROMPTS_DIR`).

## 3. Security

- Secrets via **Google Secret Manager** on Cloud Run (Langfuse keys, Pinecone/Weaviate API keys).
- Workload Identity / service account for Vertex AI — no API keys in container for Gemini.

## 4. Non-functional

- Cloud Run: 300s timeout, 2Gi memory for PDF RAG + Gemini.
- Stateless API; Chroma persistence only for PoC — use Weaviate/Pinecone in production.

## 5. Future enhancements

- ADK port of the same graph for Google Agent Builder.
- 3D/export to CAD; human-in-the-loop approval workflow.
- Scheduled re-ingestion when brand book updates.
