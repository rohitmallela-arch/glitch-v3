from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from alerts.formatter import format_shortage_change_alert
from messaging.dispatcher import MessageDispatcher
from repos.alerts_repo import AlertsRepository
from repos.delivery_log_repo import DeliveryLogRepository

log = logging.getLogger("glitch.alerts")


class AlertDispatcher:
    def __init__(self, dispatcher: Optional[MessageDispatcher] = None):
        self.dispatcher = dispatcher or MessageDispatcher()
        self.alerts = AlertsRepository()
        self.delivery = DeliveryLogRepository()

    def dispatch_telegram(self, user_id: str, chat_id: str, payload: Dict[str, Any], sweep_id: Optional[str] = None) -> Dict[str, Any]:
        rev = os.getenv("K_REVISION") or ""
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        ndc_digits = payload.get("ndc_digits")
        old_status = payload.get("old_status")
        new_status = payload.get("new_status")

        msg = format_shortage_change_alert(payload)

        t0 = time.time()
        log.info(
            "alert_send_attempt",
            extra={
                "extra": {
                    "event": "alert_send_attempt",
                    "alert_id": alert_id,
                    "user_id": user_id,
                    "channel": "telegram",
                    "ndc_digits": ndc_digits,
                    "old_status": old_status,
                    "new_status": new_status,
                    "sweep_id": sweep_id,
                    "revision": rev,
                }
            },
        )

        resp = self.dispatcher.send_telegram(chat_id=chat_id, text=msg)
        dt_ms = int((time.time() - t0) * 1000)
        ok = bool(resp.get("ok"))

        log.info(
            "alert_send_result",
            extra={
                "extra": {
                    "event": "alert_send_result",
                    "alert_id": alert_id,
                    "user_id": user_id,
                    "channel": "telegram",
                    "ok": ok,
                    "latency_ms": dt_ms,
                    "ndc_digits": ndc_digits,
                    "sweep_id": sweep_id,
                    "revision": rev,
                }
            },
        )

        self.alerts.create(
            alert_id,
            {
                "alert_id": alert_id,
                "user_id": user_id,
                "channel": "telegram",
                "ndc_digits": ndc_digits,
                "old_status": old_status,
                "new_status": new_status,
                "created_at": now,
                "ok": ok,
                "sweep_id": sweep_id,
            },
        )

        self.delivery.write(
            str(uuid.uuid4()),
            {
                "user_id": user_id,
                "channel": "telegram",
                "ndc_digits": ndc_digits,
                "created_at": now,
                "ok": ok,
                "resp": resp,
                "sweep_id": sweep_id,
                "alert_id": alert_id,
            },
        )
        return resp
