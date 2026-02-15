from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from google.cloud.firestore import Client, Transaction
from google.cloud import firestore

from storage.firestore_client import get_firestore_client


def utc_day_key(ts: datetime | None = None) -> str:
    ts = ts or datetime.now(timezone.utc)
    return ts.strftime("%Y%m%d")


class RateLimitRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def _doc_ref(self, user_id: str, day_key: str):
        return self.db.collection("users").document(user_id).collection("rate_limits").document(day_key)

    @firestore.transactional
    def reserve_quota(self, transaction: Transaction, user_id: str, ndc_digits: str, day_key: str,
                      max_total: int, max_per_ndc: int) -> Tuple[bool, str]:
        ref = self._doc_ref(user_id, day_key)
        snap = ref.get(transaction=transaction)
        data = snap.to_dict() if snap.exists else {}
        total = int(data.get("alerts_sent_total", 0))
        by_ndc = dict(data.get("alerts_sent_by_ndc", {}) or {})

        if total >= max_total:
            return False, "daily_limit"
        ndc_count = int(by_ndc.get(ndc_digits, 0))
        if ndc_count >= max_per_ndc:
            return False, "ndc_limit"

        by_ndc[ndc_digits] = ndc_count + 1
        transaction.set(ref, {
            "alerts_sent_total": total + 1,
            "alerts_sent_by_ndc": by_ndc,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, merge=True)
        return True, "ok"
