from __future__ import annotations

from typing import Any, Dict, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_ALERTS


class AlertsRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def create(self, alert_id: str, data: Dict[str, Any]) -> None:
        self.db.collection(COL_ALERTS).document(alert_id).set(data, merge=False)
