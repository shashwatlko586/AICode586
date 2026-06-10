"""Streamlit UI — Shashwat Capstone Retail layout co-pilot."""

from __future__ import annotations

import base64
import json
import os

import httpx
import streamlit as st

from cloud_run_auth import cloud_run_auth_headers

APP_NAME = os.getenv("APP_NAME", "Shashwat Capstone Retail")
APP_TAGLINE = os.getenv(
    "APP_TAGLINE",
    "Adaptive Retail Layout Design — Blue Retail Ventures",
)

API_URL = os.getenv("CLOUD_RUN_API_URL", "http://localhost:8080")

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏪",
    layout="wide",
)

st.title(APP_NAME)
st.caption(APP_TAGLINE)

with st.sidebar:
    st.header("Store parameters")
    city = st.text_input("City", value="Surat")
    store_name = st.text_input("Store name", value=f"Blue Retail {city}")
    floor_area = st.number_input("Floor area (sqm)", min_value=50.0, max_value=2000.0, value=120.0)
    keywords_raw = st.text_input(
        "Trend keywords (comma-separated)",
        value="iPhone 15, Samsung Galaxy S24, noise cancelling headphones, gaming laptop",
    )
    geo = st.text_input("Google Trends geo", value="IN")
    sub_geo = st.text_input("State geo (e.g. Gujarat)", value="IN-GJ")
    api_url = st.text_input("API URL", value=API_URL)

keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

if st.button("Generate layout", type="primary"):
    with st.spinner("Running multi-agent pipeline (Market Analyst → Strategist → Draftsman)..."):
        try:
            headers = cloud_run_auth_headers(api_url)
            resp = httpx.post(
                f"{api_url.rstrip('/')}/generate_layout",
                json={
                    "city": city,
                    "store_name": store_name,
                    "floor_area_sqm": floor_area,
                    "keywords": keywords,
                    "geo": geo,
                    "sub_geo": sub_geo,
                },
                headers=headers,
                timeout=300.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            st.error(f"API error ({exc.response.status_code}): {detail}")
            st.stop()
        except httpx.HTTPError as exc:
            st.error(f"API error: {exc}")
            st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("2D layout")
        b64 = data.get("layout_image_base64")
        if b64:
            st.image(base64.b64decode(b64), use_container_width=True)
        else:
            st.warning("No image returned.")

    with col2:
        st.subheader("Market insights")
        insights = data.get("market_insights", {})
        narrative = insights.get("narrative") if isinstance(insights, dict) else str(insights)
        st.markdown(narrative or "_No narrative_")
        raw = insights.get("raw") if isinstance(insights, dict) else {}
        if raw:
            st.json(raw.get("top_trending_products", []))

    st.subheader("Layout plan (JSON)")
    st.json(data.get("layout_plan", {}))

    if data.get("errors"):
        st.warning("Warnings: " + "; ".join(data["errors"]))

    st.caption(f"Trace ID: {data.get('trace_id', 'n/a')}")

st.divider()
st.markdown(
    """
**Agents:** Market Analyst (Google Trends) → Layout Strategist (RAG + Gemini) → AI Draftsman (Matplotlib)

**Project:** Shashwat Capstone Retail · GCP Capstone — Adaptive Retail Layout Design

Ensure the API is running and documents are ingested (`python scripts/ingest_documents.py`).
"""
)
