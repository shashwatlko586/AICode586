"""Vertex AI Gemini + embeddings with optional mock fallback."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from src.config import settings


def _has_gcp_credentials() -> bool:
    if not settings.gcp_project_id:
        return False
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    if os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT"):
        return True
    # Cloud Run / GCE — Application Default Credentials via metadata server
    if os.getenv("K_SERVICE") or os.getenv("FUNCTION_TARGET"):
        return True
    try:
        import google.auth

        google.auth.default()
        return True
    except Exception:
        return False


class VertexClient:
    def __init__(self) -> None:
        self._llm = None
        self._embeddings = None
        self.use_mock = settings.mock_llm or not _has_gcp_credentials()
        if not self.use_mock:
            self._init_vertex()

    def _init_vertex(self) -> None:
        import vertexai
        from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        self._llm = ChatVertexAI(
            model_name=settings.vertex_gemini_model,
            temperature=0.2,
            max_output_tokens=8192,
        )
        try:
            self._llm_json = ChatVertexAI(
                model_name=settings.vertex_gemini_model,
                temperature=0.1,
                max_output_tokens=8192,
                response_mime_type="application/json",
            )
        except TypeError:
            self._llm_json = self._llm
        self._embeddings = VertexAIEmbeddings(model_name=settings.vertex_embedding_model)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.use_mock:
            return [_mock_embedding(t) for t in texts]
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        if self.use_mock:
            return _mock_embedding(text)
        return self._embeddings.embed_query(text)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if self.use_mock:
            return _mock_generate(prompt)
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))
        response = self._llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if self.use_mock:
            return default_layout_plan()
        raw = self._generate_json_raw(prompt)
        return _parse_json(raw)

    def _generate_json_raw(self, prompt: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="Return a single valid JSON object. No markdown fences."),
            HumanMessage(content=prompt),
        ]
        try:
            response = self._llm_json.invoke(messages)
        except Exception:
            response = self.generate(prompt, system="Respond with valid JSON only, no markdown.")
            return response if isinstance(response, str) else str(response)
        return response.content if hasattr(response, "content") else str(response)


def _mock_embedding(text: str, dim: int | None = None) -> list[float]:
    import hashlib
    from src.config import settings

    size = dim if dim is not None else settings.embedding_dimension
    h = hashlib.sha256(text.encode()).digest()
    return [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(size)]

def _mock_generate(prompt: str) -> str:
    if "layout" in prompt.lower() or "zones" in prompt.lower():
        return json.dumps(default_layout_plan())
    return (
        "Market summary (mock mode):\n"
        "- Rising: noise cancelling headphones, gaming laptop\n"
        "- Stable: iPhone 15, Samsung Galaxy S24\n"
        "- Recommend hero placement: headphones on power wall; laptops in experience zone."
    )


def default_layout_plan(
    city: str = "Surat",
    store_name: str = "Blue Retail Surat",
    floor_area_sqm: float = 120.0,
    trending_products: list[str] | None = None,
) -> dict[str, Any]:
    trending = trending_products or ["noise cancelling headphones", "gaming laptop"]
    return {
        "store_name": store_name,
        "city": city,
        "floor_area_sqm": floor_area_sqm,
        "entrance_side": "south",
        "zones": [
            {
                "zone_type": "decompression_zone",
                "name": "Welcome",
                "x_m": 0,
                "y_m": 0,
                "width_m": 4,
                "depth_m": 4,
                "priority_products": [],
                "compliance_notes": ["Uncluttered per brand book"],
            },
            {
                "zone_type": "power_wall",
                "name": "Power Wall Right",
                "x_m": 4,
                "y_m": 0,
                "width_m": 6,
                "depth_m": 3,
                "priority_products": [trending[0]] if trending else [],
                "compliance_notes": [],
            },
            {
                "zone_type": "circulation_path",
                "name": "Main Loop",
                "x_m": 0,
                "y_m": 4,
                "width_m": 12,
                "depth_m": 2,
                "priority_products": [],
                "compliance_notes": ["Min width 1800mm NBC"],
            },
            {
                "zone_type": "experience_zone",
                "name": "Interactive Demo",
                "x_m": 2,
                "y_m": 8,
                "width_m": 8,
                "depth_m": 4,
                "priority_products": [trending[-1]] if len(trending) > 1 else trending,
                "compliance_notes": [],
            },
            {
                "zone_type": "checkout",
                "name": "Checkout",
                "x_m": 0,
                "y_m": 10,
                "width_m": 4,
                "depth_m": 2,
                "priority_products": [],
                "compliance_notes": [],
            },
        ],
        "fixtures": [
            {
                "fixture_id": "BRV-FX-HP03",
                "fixture_name": "Hero Product Pedestal",
                "x_m": 5,
                "y_m": 1,
                "width_m": 1.2,
                "depth_m": 1.2,
                "rotation_deg": 0,
                "notes": "Headphones hero",
            },
            {
                "fixture_id": "BRV-FX-IDT02",
                "fixture_name": "Interactive Display Table",
                "x_m": 4,
                "y_m": 8,
                "width_m": 2.4,
                "depth_m": 1.2,
                "rotation_deg": 0,
                "notes": "Laptop demos",
            },
        ],
        "trending_products": trending,
        "design_rationale": (
            f"Fallback layout for {store_name} in {city}: decompression zone, right power wall "
            f"with trending products, circulation loop, experience zone, and checkout."
        ),
        "compliance_checks": [
            {
                "source_document": "National_Building_Code_Accessibility_Chapter.txt",
                "requirement": "Circulation width",
                "status": "pass",
                "detail": "Main path 2000mm specified",
            }
        ],
    }


def _extract_json_text(raw: str) -> str:
    raw = raw.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
    if fenced:
        raw = fenced.group(1).strip()

    start = raw.find("{")
    if start == -1:
        return raw

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    return raw[start:]


def _parse_json(raw: str) -> dict[str, Any]:
    text = _extract_json_text(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", text)
        return json.loads(repaired)


vertex_client = VertexClient()
