from __future__ import annotations

import httpx
from typing import Any, Dict, List, Tuple

from config.settings import settings


def fetch_shortages_page(skip: int, limit: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    params = {"limit": limit, "skip": skip}
    url = settings.OPENFDA_SHORTAGE_URL
    r = httpx.get(url, params=params, timeout=30.0)
    # openFDA sometimes returns 404 when paginating beyond available results.
    # Treat that as end-of-results rather than crashing the ingest run.
    if r.status_code == 404:
        return [], {"status": "eof_404", "skip": skip, "limit": limit}
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    meta = data.get("meta") or {}
    return results, meta
