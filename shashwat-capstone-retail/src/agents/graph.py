"""LangGraph multi-agent workflow."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.draftsman import draftsman_node
from src.agents.layout_strategist import layout_strategist_node
from src.agents.market_analyst import market_analyst_node
from src.observability.langfuse_tracer import tracer
from src.state import CopilotState


def build_graph():
    workflow = StateGraph(CopilotState)
    workflow.add_node("market_analyst", market_analyst_node)
    workflow.add_node("layout_strategist", layout_strategist_node)
    workflow.add_node("draftsman", draftsman_node)

    workflow.set_entry_point("market_analyst")
    workflow.add_edge("market_analyst", "layout_strategist")
    workflow.add_edge("layout_strategist", "draftsman")
    workflow.add_edge("draftsman", END)

    return workflow.compile()


compiled_graph = build_graph()


def run_copilot(
    city: str = "Surat",
    store_name: str = "Blue Retail Surat",
    floor_area_sqm: float = 120.0,
    keywords: list[str] | None = None,
    geo: str = "IN",
    sub_geo: str = "IN-GJ",
) -> CopilotState:
    trace_id = tracer.new_trace_id()
    initial: CopilotState = {
        "city": city,
        "store_name": store_name,
        "floor_area_sqm": floor_area_sqm,
        "keywords": keywords,
        "geo": geo,
        "sub_geo": sub_geo,
        "trace_id": trace_id,
        "errors": [],
    }

    with tracer.trace("generate_layout", trace_id=trace_id, metadata={"city": city}):
        result = compiled_graph.invoke(initial)
    result["trace_id"] = trace_id
    return result
