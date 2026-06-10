"""LangGraph shared state for the Architect Copilot."""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class CopilotState(TypedDict, total=False):
    city: str
    store_name: str
    floor_area_sqm: float
    keywords: list[str]
    geo: str
    sub_geo: str

    market_insights: dict[str, Any]
    top_trending_products: list[str]
    retrieved_context: list[dict[str, Any]]
    layout_plan_json: dict[str, Any]
    layout_plan_valid: bool
    layout_image_path: str
    errors: list[str]
    trace_id: Optional[str]
