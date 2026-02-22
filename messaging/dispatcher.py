from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from messaging.telegram import TelegramClient
from messaging.sms import SmsClient

log = logging.getLogger("glitch.dispatcher")


def _dest_hint(v: str, keep: int = 4) -> str:
    v = (v or "").strip()
    if not v:
        return ""
    if len(v) <= keep:
        return v
    return f"...{v[-keep:]}"


class MessageDispatcher:
    def __init__(self, telegram: Optional[TelegramClient] = None, sms: Optional[SmsClient] = None):
        self.telegram = telegram
        self.sms = sms

    def send_telegram(self, chat_id: str, text: str) -> Dict[str, Any]:
        rev = os.getenv("K_REVISION") or ""
        t0 = time.time()
        log.info(
            "message_send_attempt",
            extra={"extra": {"event": "message_send_attempt", "channel": "telegram", "dest": _dest_hint(chat_id), "revision": rev}},
        )
        try:
            if not self.telegram:
                self.telegram = TelegramClient()
            resp = self.telegram.send_message(chat_id=chat_id, text=text)
            dt_ms = int((time.time() - t0) * 1000)
            log.info(
                "message_send_result",
                extra={
                    "extra": {
                        "event": "message_send_result",
                        "channel": "telegram",
                        "dest": _dest_hint(chat_id),
                        "ok": bool(resp.get("ok", False)),
                        "latency_ms": dt_ms,
                        "revision": rev,
                    }
                },
            )
            return resp
        except Exception as e:
            dt_ms = int((time.time() - t0) * 1000)
            log.error(
                "message_send_exception",
                extra={
                    "extra": {
                        "event": "message_send_exception",
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

    def send_sms(self, to_number: str, text: str) -> Dict[str, Any]:
        rev = os.getenv("K_REVISION") or ""
        t0 = time.time()
        log.info(
            "message_send_attempt",
            extra={"extra": {"event": "message_send_attempt", "channel": "sms", "dest": _dest_hint(to_number), "revision": rev}},
        )
        try:
            if not self.sms:
                self.sms = SmsClient()
            resp = self.sms.send_message(to_number=to_number, text=text)
            dt_ms = int((time.time() - t0) * 1000)
            log.info(
                "message_send_result",
                extra={
                    "extra": {
                        "event": "message_send_result",
                        "channel": "sms",
                        "dest": _dest_hint(to_number),
                        "ok": bool(resp.get("ok", False)),
                        "latency_ms": dt_ms,
                        "revision": rev,
                    }
                },
            )
            return resp
        except Exception as e:
            dt_ms = int((time.time() - t0) * 1000)
            log.error(
                "message_send_exception",
                extra={
                    "extra": {
                        "event": "message_send_exception",
                        "channel": "sms",
                        "dest": _dest_hint(to_number),
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "latency_ms": dt_ms,
                        "revision": rev,
                    }
                },
                exc_info=True,
            )
            return {"ok": False, "error_type": type(e).__name__, "message": str(e)}
