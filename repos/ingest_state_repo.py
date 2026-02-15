from __future__ import annotations

from typing import Any, Dict, Optional
from google.cloud import firestore
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_SYSTEM, DOC_INGEST_STATE


class IngestStateRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def get_state(self) -> Dict[str, Any]:
        ref = self.db.collection(COL_SYSTEM).document(DOC_INGEST_STATE)
        snap = ref.get()
        if not snap.exists:
            return {"baseline_completed": False}
        data = snap.to_dict() or {}
        if "baseline_completed" not in data:
            data["baseline_completed"] = False
        return data

    def set_baseline_completed(self) -> None:
        ref = self.db.collection(COL_SYSTEM).document(DOC_INGEST_STATE)
        ref.set({"baseline_completed": True, "baseline_completed_at": firestore.SERVER_TIMESTAMP}, merge=True)

    def update_sweep_metrics(self, metrics: Dict[str, Any]) -> None:
        ref = self.db.collection(COL_SYSTEM).document(DOC_INGEST_STATE)
        ref.set(metrics, merge=True)
