"""Document loading and chunking for RAG ingestion."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)

DOCUMENT_SOURCES = {
    "Blue_Retail_Brand_Book_v4.pdf": "brand_book",
    "Fixture_Catalog_Q3_2025.pdf": "fixture_catalog",
    "National_Building_Code_Accessibility_Chapter.txt": "building_code",
    "Store_Leasing_Agreement_Surat.pdf": "leasing_agreement",
    "Retail_Design_Best_Practices.md.txt": "best_practices",
    "Retail_Design_Best_Practices.md": "best_practices",
}


def load_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts)
    return path.read_text(encoding="utf-8", errors="replace")


def iter_document_chunks(resources_dir: Path | None = None) -> Iterator[dict]:
    base = resources_dir or settings.resources_dir
    if not base.exists():
        raise FileNotFoundError(f"Resources directory not found: {base}")

    for filename, source_tag in DOCUMENT_SOURCES.items():
        path = base / filename
        if not path.exists():
            continue
        text = load_text_from_file(path)
        if not text.strip():
            continue
        for i, chunk in enumerate(SPLITTER.split_text(text)):
            yield {
                "text": chunk,
                "metadata": {
                    "source_document": source_tag,
                    "filename": filename,
                    "chunk_index": i,
                },
            }
