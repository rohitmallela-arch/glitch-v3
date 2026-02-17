from __future__ import annotations

from typing import Any, Dict, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_USERS


class UserRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        snap = self.db.collection(COL_USERS).document(user_id).get()
        if not snap.exists:
            return None
        d = snap.to_dict() or {}
        d["user_id"] = user_id
        return d

    def create_if_absent(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        ref = self.db.collection(COL_USERS).document(user_id)
        snap = ref.get()
        if snap.exists:
            return snap.to_dict() or {"user_id": user_id}
        ref.set({**data, "created_at": firestore.SERVER_TIMESTAMP}, merge=False)
        return {**data, "user_id": user_id}

    def update(self, user_id: str, data: Dict[str, Any]) -> None:
        self.db.collection(COL_USERS).document(user_id).set(data, merge=True)
