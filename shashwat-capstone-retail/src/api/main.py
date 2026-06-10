"""FastAPI wrapper for Architect Copilot."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.agents.graph import run_copilot
from src.config import settings
from src.rag.vector_store import get_vector_store

app = FastAPI(
    title="Shashwat Capstone Retail API",
    description="AI Co-pilot for Adaptive Retail Layout Design — Blue Retail Ventures",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateLayoutRequest(BaseModel):
    city: str = Field(default="Surat", examples=["Surat"])
    store_name: str = Field(default="Blue Retail Surat")
    floor_area_sqm: float = Field(default=120.0, gt=0, le=2000)
    keywords: Optional[list[str]] = None
    geo: str = "IN"
    sub_geo: str = "IN-GJ"


class GenerateLayoutResponse(BaseModel):
    city: str
    store_name: str
    layout_plan: dict
    layout_plan_valid: bool
    market_insights: dict
    layout_image_path: str
    layout_image_base64: Optional[str] = None
    trace_id: Optional[str] = None
    errors: list[str] = []


@app.get("/health")
def health():
    try:
        count = get_vector_store().count()
    except Exception:
        count = -1
    return {
        "status": "ok",
        "vector_db": settings.vector_db_provider,
        "env_vector_db": os.getenv("VECTOR_DB_PROVIDER"),
        "indexed_chunks": count,
        "mock_llm": settings.mock_llm,
        "mock_trends": settings.mock_trends,
    }


@app.post("/generate_layout", response_model=GenerateLayoutResponse)
def generate_layout(req: GenerateLayoutRequest):
    try:
        result = run_copilot(
            city=req.city,
            store_name=req.store_name,
            floor_area_sqm=req.floor_area_sqm,
            keywords=req.keywords,
            geo=req.geo,
            sub_geo=req.sub_geo,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    image_b64 = None
    img_path = result.get("layout_image_path")
    if img_path and Path(img_path).exists():
        image_b64 = base64.b64encode(Path(img_path).read_bytes()).decode()

    return GenerateLayoutResponse(
        city=req.city,
        store_name=req.store_name,
        layout_plan=result.get("layout_plan_json") or {},
        layout_plan_valid=bool(result.get("layout_plan_valid")),
        market_insights=result.get("market_insights") or {},
        layout_image_path=img_path or "",
        layout_image_base64=image_b64,
        trace_id=result.get("trace_id"),
        errors=result.get("errors") or [],
    )


@app.get("/")
def root():
    return JSONResponse(
        {
            "service": "Shashwat Capstone Retail",
            "docs": "/docs",
            "endpoints": ["/health", "/generate_layout"],
        }
    )
