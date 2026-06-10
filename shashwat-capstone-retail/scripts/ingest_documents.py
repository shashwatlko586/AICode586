#!/usr/bin/env python3
"""Ingest Resources into vector DB (Weaviate / Pinecone / Chroma)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import settings
from src.rag.chunking import iter_document_chunks
from src.rag.vector_store import get_vector_store


def main() -> None:
    print(f"Resources: {settings.resources_dir}")
    print(f"Vector DB: {settings.vector_db_provider}")
    chunks = list(iter_document_chunks())
    if not chunks:
        print("No documents found. Check RESOURCES_DIR.")
        sys.exit(1)
    print(f"Chunks to upsert: {len(chunks)}")
    store = get_vector_store()
    n = store.upsert_chunks(chunks)
    print(f"Upserted {n} chunks. Index count: {store.count()}")


if __name__ == "__main__":
    main()
