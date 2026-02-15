from __future__ import annotations

from typing import Any, Dict, List, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_WATCHLISTS


class WatchlistRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def _items_col(self, user_id: str):
        return self.db.collection(COL_WATCHLISTS).document(user_id).collection("items")

    def list_ndcs(self, user_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        docs = self._items_col(user_id).limit(limit).stream()
        out = []
        for d in docs:
            item = d.to_dict() or {}
            item["ndc_digits"] = d.id
            out.append(item)
        return out

    def count(self, user_id: str) -> int:
        # Firestore count aggregation is available but varies; use stream for simplicity.
        return sum(1 for _ in self._items_col(user_id).stream())

    def add(self, user_id: str, ndc_digits: str, data: Dict[str, Any]) -> None:
        self._items_col(user_id).document(ndc_digits).set({**data, "ndc_digits": ndc_digits}, merge=True)

    def remove(self, user_id: str, ndc_digits: str) -> None:
        self._items_col(user_id).document(ndc_digits).delete()
