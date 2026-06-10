"""AI Draftsman — renders 2D layout PNG from JSON plan."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from src.config import settings
from src.observability.langfuse_tracer import tracer
from src.state import CopilotState

ZONE_COLORS = {
    "decompression_zone": "#E8F4FC",
    "power_wall": "#FFE4B5",
    "circulation_path": "#F0F0F0",
    "merchandising": "#E6FFE6",
    "experience_zone": "#E6E6FA",
    "checkout": "#FFDAB9",
    "service_desk": "#DDA0DD",
    "bopis_pickup": "#B0E0E6",
    "storage": "#D3D3D3",
}


def render_layout_png(plan: dict, output_path: Path) -> Path:
    zones = plan.get("zones", [])
    fixtures = plan.get("fixtures", [])
    floor_area = plan.get("floor_area_sqm", 120.0)
    aspect = 1.4
    height = (floor_area / aspect) ** 0.5
    width = floor_area / height

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, max(width, 12))
    ax.set_ylim(0, max(height, 10))
    ax.set_aspect("equal")
    ax.set_xlabel("Meters")
    ax.set_ylabel("Meters")
    ax.set_title(
        f"{plan.get('store_name', 'Store')} — {plan.get('city', '')} "
        f"({floor_area:.0f} sqm)"
    )

    for z in zones:
        zt = z.get("zone_type", "merchandising")
        color = ZONE_COLORS.get(zt, "#FFFFFF")
        rect = patches.Rectangle(
            (z["x_m"], z["y_m"]),
            z["width_m"],
            z["depth_m"],
            linewidth=1.5,
            edgecolor="#333333",
            facecolor=color,
            alpha=0.7,
        )
        ax.add_patch(rect)
        cx = z["x_m"] + z["width_m"] / 2
        cy = z["y_m"] + z["depth_m"] / 2
        ax.text(cx, cy, z.get("name", zt), ha="center", va="center", fontsize=8, wrap=True)

    for f in fixtures:
        rect = patches.Rectangle(
            (f["x_m"], f["y_m"]),
            f["width_m"],
            f["depth_m"],
            linewidth=2,
            edgecolor="#1a5276",
            facecolor="#85c1e9",
            alpha=0.9,
        )
        ax.add_patch(rect)
        ax.text(
            f["x_m"] + f["width_m"] / 2,
            f["y_m"] + f["depth_m"] / 2,
            f.get("fixture_id", ""),
            ha="center",
            va="center",
            fontsize=7,
            color="white",
            weight="bold",
        )

    # Entrance marker
    entrance = plan.get("entrance_side", "south")
    ax.annotate(
        f"ENTRANCE ({entrance})",
        xy=(width / 2, 0.2),
        fontsize=10,
        color="red",
        ha="center",
        weight="bold",
    )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def draftsman_node(state: CopilotState) -> dict:
    plan = state.get("layout_plan_json") or {}
    trace_id = state.get("trace_id")
    city = state.get("city", "surat").lower().replace(" ", "_")
    out_name = f"layout_{city}_{state.get('store_name', 'store')}.png".replace(" ", "_")
    out_path = settings.output_dir / out_name

    path = render_layout_png(plan, out_path)

    if trace_id:
        tracer.log_span(
            trace_id,
            "draftsman",
            input_data={"zones": len(plan.get("zones", []))},
            output_data={"image_path": str(path)},
        )

    return {"layout_image_path": str(path)}
