"""Google Trends tool for Market Analyst agent (pytrends + mock)."""

from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any

import pandas as pd

from src.config import settings

DEFAULT_KEYWORDS = [
    "iPhone 15",
    "Samsung Galaxy S24",
    "noise cancelling headphones",
    "gaming laptop",
]


def _mock_interest_over_time(keywords: list[str], periods: int = 168) -> pd.DataFrame:
    idx = pd.date_range(end=pd.Timestamp.now().floor("h"), periods=periods, freq="h")
    data = {}
    for kw in keywords:
        base = random.randint(20, 60)
        series = pd.Series(
            [max(0, base + random.randint(-5, 5)) for _ in range(periods)],
            index=idx,
        )
        data[kw] = series
    df = pd.DataFrame(data)
    df.index.name = "datetime"
    return df


def fetch_market_trends(
    keywords: list[str] | None = None,
    geo: str = "IN",
    sub_geo: str = "IN-GJ",
    timeframe: str = "now 7-d",
    gprop: str = "froogle",
) -> dict[str, Any]:
    keywords = keywords or DEFAULT_KEYWORDS
    use_mock = settings.mock_trends

    if not use_mock:
        try:
            from pytrends.request import TrendReq

            pytrend = TrendReq(hl="en-US", tz=330)
            pytrend.build_payload(kw_list=keywords[:5], timeframe=timeframe, geo=geo, gprop=gprop)
            iot = pytrend.interest_over_time()
            if "isPartial" in iot.columns:
                iot = iot.drop(columns=["isPartial"])

            # State-level proxy for Surat / Gujarat
            pytrend.build_payload(
                kw_list=keywords[:5], timeframe=timeframe, geo=sub_geo, gprop=gprop
            )
            iot_state = pytrend.interest_over_time()
            if "isPartial" in iot_state.columns:
                iot_state = iot_state.drop(columns=["isPartial"])

            summary = _summarize_interest(iot, keywords)
            state_summary = _summarize_interest(iot_state, keywords)
            top_products = _rank_products(summary, state_summary)

            return {
                "geo": geo,
                "sub_geo": sub_geo,
                "timeframe": timeframe,
                "keywords": keywords,
                "national_summary": summary,
                "state_summary": state_summary,
                "top_trending_products": top_products,
                "fetched_at": datetime.utcnow().isoformat() + "Z",
                "mock": False,
            }
        except Exception as exc:
            use_mock = True
            error = str(exc)
    else:
        error = None

    iot = _mock_interest_over_time(keywords)
    summary = _summarize_interest(iot, keywords)
    return {
        "geo": geo,
        "sub_geo": sub_geo,
        "timeframe": timeframe,
        "keywords": keywords,
        "national_summary": summary,
        "state_summary": summary,
        "top_trending_products": _rank_products(summary, summary),
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "mock": True,
        "error": error,
    }


def _summarize_interest(df: pd.DataFrame, keywords: list[str]) -> dict[str, dict]:
    out = {}
    for kw in keywords:
        if kw not in df.columns:
            continue
        series = df[kw]
        out[kw] = {
            "mean_interest": float(series.mean()),
            "latest": float(series.iloc[-1]),
            "trend": "rising" if series.iloc[-1] > series.iloc[0] else "declining",
        }
    return out


def _rank_products(
    national: dict[str, dict],
    state: dict[str, dict],
) -> list[str]:
    scores = {}
    for kw in set(national) | set(state):
        n = national.get(kw, {}).get("mean_interest", 0)
        s = state.get(kw, {}).get("mean_interest", 0)
        scores[kw] = n * 0.4 + s * 0.6
    ranked = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    return ranked[:5]


def trends_to_summary_text(data: dict[str, Any]) -> str:
    return json.dumps(
        {
            "top_trending": data.get("top_trending_products"),
            "national": data.get("national_summary"),
            "state": data.get("state_summary"),
            "mock": data.get("mock"),
        },
        indent=2,
    )
