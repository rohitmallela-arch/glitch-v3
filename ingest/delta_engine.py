from __future__ import annotations

import hashlib
from typing import Any, Dict


def snapshot_hash(record: Dict[str, Any]) -> str:
    relevant = {
        "status": record.get("status"),
        "shortage_start_date": record.get("shortage_start_date"),
        "shortage_end_date": record.get("shortage_end_date"),
        "last_updated": record.get("last_updated"),
        "presentation": record.get("presentation"),
        "reason": record.get("reason"),
        "resolution": record.get("resolution"),
    }
    s = str(sorted(relevant.items())).encode("utf-8")
    return hashlib.sha256(s).hexdigest()
