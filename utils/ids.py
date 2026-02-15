from __future__ import annotations

import hashlib

def user_id_from_phone_e164(phone_e164: str) -> str:
    # Deterministic, privacy-preserving user_id derived from phone.
    # Matches legacy pattern: u_ + sha256(phone_e164).
    phone = (phone_e164 or "").strip()
    if not phone:
        return ""
    h = hashlib.sha256(phone.encode("utf-8")).hexdigest()
    return f"u_{h}"
