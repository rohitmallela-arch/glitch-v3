from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from config.settings import settings

log = logging.getLogger("glitch.telegram")


class TelegramClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
        r = httpx.post(url, json=payload, timeout=20.0)
        try:
            data = r.json()
        except Exception:
            data = {"ok": False, "status_code": r.status_code, "text": r.text[:500]}
        if not data.get("ok", False):
            log.warning("telegram send failed", extra={"extra": {"status_code": r.status_code, "resp": data}})
        return data
