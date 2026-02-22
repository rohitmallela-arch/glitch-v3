from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from config.settings import settings

log = logging.getLogger("glitch.telegram")


def _dest_hint(v: str, keep: int = 4) -> str:
    v = (v or "").strip()
    if not v:
        return ""
    if len(v) <= keep:
        return v
    return f"...{v[-keep:]}"


class TelegramClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        rev = os.getenv("K_REVISION") or ""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}

        t0 = time.time()
        log.info(
            "telegram_send_attempt",
            extra={"extra": {"event": "telegram_send_attempt", "channel": "telegram", "dest": _dest_hint(chat_id), "revision": rev}},
        )

        try:
            r = httpx.post(url, json=payload, timeout=20.0)
            try:
                data = r.json()
            except Exception:
                data = {"ok": False, "status_code": r.status_code, "text": (r.text or "")[:500]}

            dt_ms = int((time.time() - t0) * 1000)
            ok = bool(data.get("ok", False))
            log.info(
                "telegram_send_result",
                extra={
                    "extra": {
                        "event": "telegram_send_result",
                        "channel": "telegram",
                        "dest": _dest_hint(chat_id),
                        "ok": ok,
                        "status_code": int(getattr(r, "status_code", 0) or 0),
                        "latency_ms": dt_ms,
                        "revision": rev,
                    }
                },
            )

            if not ok:
                log.warning(
                    "telegram_send_failed",
                    extra={"extra": {"event": "telegram_send_failed", "status_code": r.status_code, "resp": data, "revision": rev}},
                )
            return data
        except Exception as e:
            dt_ms = int((time.time() - t0) * 1000)
            log.error(
                "telegram_send_exception",
                extra={
                    "extra": {
                        "event": "telegram_send_exception",
                        "channel": "telegram",
                        "dest": _dest_hint(chat_id),
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "latency_ms": dt_ms,
                        "revision": rev,
                    }
                },
                exc_info=True,
            )
            return {"ok": False, "error_type": type(e).__name__, "message": str(e)}
