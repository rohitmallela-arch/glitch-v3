from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from messaging.telegram import TelegramClient
from messaging.sms import SmsClient

log = logging.getLogger("glitch.dispatcher")


class MessageDispatcher:
    def __init__(self, telegram: Optional[TelegramClient] = None, sms: Optional[SmsClient] = None):
        self.telegram = telegram
        self.sms = sms

    def send_telegram(self, chat_id: str, text: str) -> Dict[str, Any]:
        if not self.telegram:
            self.telegram = TelegramClient()
        return self.telegram.send_message(chat_id=chat_id, text=text)

    def send_sms(self, to_number: str, text: str) -> Dict[str, Any]:
        if not self.sms:
            self.sms = SmsClient()
        return self.sms.send_message(to_number=to_number, text=text)
