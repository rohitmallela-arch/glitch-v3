from __future__ import annotations

# SMS is intentionally abstracted. Twilio wiring can be enabled later.
# For now we keep an interface-compatible client.

from typing import Any, Dict


class SmsClient:
    def send_message(self, to_number: str, text: str) -> Dict[str, Any]:
        raise NotImplementedError("SMS sending not enabled (A2P gated)")
