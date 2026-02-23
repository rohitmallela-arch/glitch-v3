from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud.firestore import Client

from storage.firestore_client import get_firestore_client


COL_TELEGRAM_CHAT_TO_USER = "telegram_chat_to_user"


class TelegramChatIndexRepository:
    """
    Reverse index enforcing: telegram_chat_id -> canonical_user_id

    This prevents multiple user docs from being linked to the same Telegram chat.
    """
    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()

    def get(self, chat_id: str) -> Dict[str, Any]:
        chat_id = str(chat_id or "").strip()
        if not chat_id:
            return {}
        snap = self.db.collection(COL_TELEGRAM_CHAT_TO_USER).document(chat_id).get()
        return snap.to_dict() or {}

    def set(self, chat_id: str, canonical_user_id: str) -> None:
        chat_id = str(chat_id or "").strip()
        canonical_user_id = str(canonical_user_id or "").strip()
        if not chat_id or not canonical_user_id:
            raise ValueError("chat_id and canonical_user_id are required")
        self.db.collection(COL_TELEGRAM_CHAT_TO_USER).document(chat_id).set(
            {
                "canonical_user_id": canonical_user_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            merge=True,
        )
