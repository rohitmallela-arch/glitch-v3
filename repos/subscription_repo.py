from __future__ import annotations

from typing import Any, Dict, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_SUBSCRIPTIONS


class SubscriptionRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def get_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        snap = self.db.collection(COL_SUBSCRIPTIONS).document(user_id).get()
        if not snap.exists:
            return None
        d = snap.to_dict() or {}
        d["user_id"] = user_id
        return d

    def upsert(self, user_id: str, data: Dict[str, Any]) -> None:
        self.db.collection(COL_SUBSCRIPTIONS).document(user_id).set(data, merge=True)
