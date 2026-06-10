"""Identity token auth for private Cloud Run services."""

from __future__ import annotations

import os


def cloud_run_auth_headers(api_url: str) -> dict[str, str]:
    """Return auth headers only when CLOUD_RUN_USE_AUTH=true (private Cloud Run)."""
    if os.getenv("CLOUD_RUN_USE_AUTH", "").lower() not in ("1", "true", "yes"):
        return {}

    if "localhost" in api_url or "127.0.0.1" in api_url:
        return {}

    audience = api_url.rstrip("/").split("/", 3)
    audience = "/".join(audience[:3]) if len(audience) >= 3 else api_url.rstrip("/")

    import google.auth.transport.requests
    import google.oauth2.id_token

    token = google.oauth2.id_token.fetch_id_token(
        google.auth.transport.requests.Request(),
        audience,
    )
    return {"Authorization": f"Bearer {token}"}
