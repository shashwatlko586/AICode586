"""Market Analyst agent node."""

from __future__ import annotations

from src.llm.vertex_client import vertex_client
from src.observability.langfuse_tracer import tracer
from src.prompts.render import render_prompt
from src.state import CopilotState
from src.tools.trends import fetch_market_trends, trends_to_summary_text


def _load_prompt_template() -> str:
    from src.config import settings

    path = settings.prompts_dir / "market_analyst_v1.txt"
    return path.read_text(encoding="utf-8")


def market_analyst_node(state: CopilotState) -> dict:
    city = state.get("city", "Surat")
    geo = state.get("geo", "IN")
    sub_geo = state.get("sub_geo", "IN-GJ")
    keywords = state.get("keywords") or None
    trace_id = state.get("trace_id")

    trend_data = fetch_market_trends(keywords=keywords, geo=geo, sub_geo=sub_geo)
    summary_text = trends_to_summary_text(trend_data)

    prompt = render_prompt(
        _load_prompt_template(),
        city=city,
        geo=geo,
        sub_geo=sub_geo,
        trend_summary=summary_text,
    )
    narrative = vertex_client.generate(prompt)

    if trace_id:
        tracer.log_span(
            trace_id,
            "market_analyst",
            input_data={"city": city, "geo": geo},
            output_data={"trends": trend_data, "narrative": narrative[:500]},
        )

    return {
        "market_insights": {
            "raw": trend_data,
            "narrative": narrative,
        },
        "top_trending_products": trend_data.get("top_trending_products", []),
    }
