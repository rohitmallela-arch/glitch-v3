from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Tuple

# Deterministic fail-closed limits are enforced by counting in Firestore delivery_logs.
# To keep this portable and fast, we implement policy logic here and do counting in services.

def utc_day_key(ts: datetime | None = None) -> str:
    ts = ts or datetime.now(timezone.utc)
    return ts.strftime("%Y-%m-%d")


class RateLimitPolicy:
    def __init__(self, max_alerts_per_day: int, max_alerts_per_ndc_per_day: int):
        self.max_alerts_per_day = max_alerts_per_day
        self.max_alerts_per_ndc_per_day = max_alerts_per_ndc_per_day
