"""Application configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Cloud Run sets K_SERVICE — use platform env vars there, not a baked-in .env file
if not os.getenv("K_SERVICE"):
    load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESOURCES = PROJECT_ROOT.parent / "Resources"


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes")


class Settings:
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "")
    gcp_location: str = os.getenv("GCP_LOCATION", "us-central1")
    vertex_gemini_model: str = os.getenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash")
    vertex_embedding_model: str = os.getenv("VERTEX_EMBEDDING_MODEL", "text-embedding-005")

    vector_db_provider: str = os.getenv("VECTOR_DB_PROVIDER", "pinecone").lower()
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_api_key: str = os.getenv("WEAVIATE_API_KEY", "")
    weaviate_class_name: str = os.getenv("WEAVIATE_CLASS_NAME", "RetailDesignChunk")
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "retail-layout-rag")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "768"))

    mock_llm: bool = _bool("MOCK_LLM")
    mock_trends: bool = _bool("MOCK_TRENDS")

    resources_dir: Path = Path(os.getenv("RESOURCES_DIR", str(DEFAULT_RESOURCES)))
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs")))
    prompts_dir: Path = Path(os.getenv("PROMPTS_DIR", str(PROJECT_ROOT / "prompts")))
    chroma_persist_dir: Path = Path(
        os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "data" / "chroma"))
    )

    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8080"))


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
if settings.vector_db_provider == "chroma":
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
