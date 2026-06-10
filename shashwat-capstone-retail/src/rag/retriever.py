"""RAG retrieval for Layout Strategist."""

from __future__ import annotations

from typing import Any

from src.rag.vector_store import get_vector_store


def retrieve_for_layout(
    city: str,
    floor_area_sqm: float,
    trending_products: list[str],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    products = ", ".join(trending_products) if trending_products else "consumer electronics"
    query = (
        f"Retail store layout for {city}, floor area {floor_area_sqm} sqm. "
        f"Products: {products}. Brand guidelines, accessibility NBC, leasing constraints, fixtures."
    )
    store = get_vector_store()
    chunks = store.query(query, top_k=top_k)

    # Boost leasing and building code with targeted queries
    for extra_q in [
        "leasing agreement surat store constraints signage height",
        "accessibility ramp width circulation NBC 2016",
        "decompression zone power wall circulation Blue Retail",
    ]:
        chunks.extend(store.query(extra_q, top_k=3))

    seen = set()
    unique = []
    for c in chunks:
        key = c["text"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique[:top_k + 5]


def format_retrieved_context(chunks: list[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata", {})
        src = meta.get("source_document", "unknown")
        lines.append(f"[{i}] source={src}\n{c['text'][:800]}\n")
    return "\n".join(lines)
