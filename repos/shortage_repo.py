from __future__ import annotations

from typing import Any, Dict, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_SHORTAGES


class ShortageRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def get(self, ndc_digits: str) -> Optional[Dict[str, Any]]:
        snap = self.db.collection(COL_SHORTAGES).document(ndc_digits).get()
        if not snap.exists:
            return None
        d = snap.to_dict() or {}
        d["ndc_digits"] = ndc_digits
        return d

    def upsert(self, ndc_digits: str, data: Dict[str, Any]) -> None:
        self.db.collection(COL_SHORTAGES).document(ndc_digits).set(data, merge=True)
