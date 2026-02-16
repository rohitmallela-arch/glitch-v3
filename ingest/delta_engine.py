from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def snapshot_hash(record: Dict[str, Any]) -> str:
    """
    Stable snapshot hash for *content change* detection.
    Includes last_updated because a real upstream update should trigger delta.
    """
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


def variant_key(record: Dict[str, Any]) -> str:
    """
    Stable identity key for variant-level storage.

    IMPORTANT:
    - Must NOT include 'last_updated' (otherwise routine updates create new variant docs).
    - Must be deterministic for the same variant presentation/status identity.
    """
    identity = {
        "status": (record.get("status") or "").strip(),
        "presentation": (record.get("presentation") or "").strip(),
        "shortage_start_date": (record.get("shortage_start_date") or "").strip(),
        "shortage_end_date": (record.get("shortage_end_date") or "").strip(),
        "reason": (record.get("reason") or "").strip(),
        "resolution": (record.get("resolution") or "").strip(),
    }
    b = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(b).hexdigest()
