from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_NDC_WATCHERS


class NDCWatchersRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def _watchers_col(self, ndc_digits: str):
        return self.db.collection(COL_NDC_WATCHERS).document(ndc_digits).collection("watchers")

    def add_watcher(self, ndc_digits: str, user_id: str, data: Dict[str, Any] | None = None) -> None:
        self._watchers_col(ndc_digits).document(user_id).set(data or {"user_id": user_id}, merge=True)

    def remove_watcher(self, ndc_digits: str, user_id: str) -> None:
        self._watchers_col(ndc_digits).document(user_id).delete()

    def iter_watchers(self, ndc_digits: str, limit: int = 5000) -> Iterable[str]:
        for snap in self._watchers_col(ndc_digits).limit(limit).stream():
            yield snap.id
