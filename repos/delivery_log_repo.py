from __future__ import annotations

from typing import Any, Dict, Optional
from google.cloud.firestore import Client
from storage.firestore_client import get_firestore_client
from models.schema import COL_DELIVERY_LOGS


class DeliveryLogRepository:
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def write(self, log_id: str, data: Dict[str, Any]) -> None:
        self.db.collection(COL_DELIVERY_LOGS).document(log_id).set(data, merge=False)
