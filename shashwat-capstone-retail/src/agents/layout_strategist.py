"""Layout Strategist agent — RAG + Vertex Gemini JSON plan."""

from __future__ import annotations

import json

from pydantic import ValidationError

from src.llm.vertex_client import default_layout_plan, vertex_client
from src.observability.langfuse_tracer import tracer
from src.prompts.render import render_prompt
from src.rag.retriever import format_retrieved_context, retrieve_for_layout
from src.schemas.layout_plan import LayoutPlan
from src.state import CopilotState


def _load_prompt_template() -> str:
    from src.config import settings

    return (settings.prompts_dir / "layout_strategist_v1.txt").read_text(encoding="utf-8")


def _build_layout_plan(
    prompt: str,
    city: str,
    store_name: str,
    floor_area: float,
    trending: list[str],
    errors: list[str],
) -> tuple[dict, bool]:
    retry_suffix = (
        "\n\nReturn ONLY one compact JSON object. "
        "Keep design_rationale under 200 characters. Escape double quotes inside strings."
    )
    for attempt, suffix in enumerate(("", retry_suffix), start=1):
        try:
            plan_dict = vertex_client.generate_json(prompt + suffix)
            plan = LayoutPlan.model_validate(plan_dict)
            return plan.model_dump(mode="json"), True
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"Layout parse attempt {attempt} failed: {exc}")

    errors.append("Using fallback layout plan after JSON parse failures.")
    fallback = default_layout_plan(
        city=city,
        store_name=store_name,
        floor_area_sqm=floor_area,
        trending_products=trending,
    )
    plan = LayoutPlan.model_validate(fallback)
    return plan.model_dump(mode="json"), False


def layout_strategist_node(state: CopilotState) -> dict:
    city = state.get("city", "Surat")
    store_name = state.get("store_name", f"Blue Retail {city}")
    floor_area = state.get("floor_area_sqm", 120.0)
    trending = state.get("top_trending_products") or []
    trace_id = state.get("trace_id")
    errors = list(state.get("errors") or [])

    chunks = retrieve_for_layout(city, floor_area, trending)
    context_str = format_retrieved_context(chunks)
    market = state.get("market_insights", {})
    market_str = json.dumps(market, indent=2)[:4000]

    prompt = render_prompt(
        _load_prompt_template(),
        city=city,
        store_name=store_name,
        floor_area_sqm=floor_area,
        trending_products=", ".join(trending),
        retrieved_context=context_str,
        market_insights=market_str,
    )

    if trace_id:
        tracer.log_span(
            trace_id,
            "rag_retrieval",
            input_data={"city": city, "floor_area": floor_area},
            output_data={"chunk_count": len(chunks), "sources": [c.get("metadata") for c in chunks[:5]]},
        )

    plan_dict, valid = _build_layout_plan(prompt, city, store_name, floor_area, trending, errors)

    if trace_id:
        tracer.log_span(
            trace_id,
            "layout_strategist",
            input_data={"prompt_chars": len(prompt)},
            output_data={"valid": valid, "zones": len(plan_dict.get("zones", []))},
        )

    return {
        "retrieved_context": chunks,
        "layout_plan_json": plan_dict,
        "layout_plan_valid": valid,
        "errors": errors,
    }
