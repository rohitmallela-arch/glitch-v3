from __future__ import annotations

import logging
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
        msg = format_shortage_change_alert(payload)
        resp = self.dispatcher.send_telegram(chat_id=chat_id, text=msg)
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        self.alerts.create(alert_id, {
            "alert_id": alert_id,
            "user_id": user_id,
            "channel": "telegram",
            "ndc_digits": payload.get("ndc_digits"),
            "old_status": payload.get("old_status"),
            "new_status": payload.get("new_status"),
            "created_at": now,
            "ok": bool(resp.get("ok")),
            "sweep_id": sweep_id,
        })

        self.delivery.write(str(uuid.uuid4()), {
            "user_id": user_id,
            "channel": "telegram",
            "ndc_digits": payload.get("ndc_digits"),
            "created_at": now,
            "ok": bool(resp.get("ok")),
            "resp": resp,
            "sweep_id": sweep_id,
        })
        return resp
