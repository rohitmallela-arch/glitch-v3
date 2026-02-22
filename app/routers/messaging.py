from __future__ import annotations

import time

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from messaging.dispatcher import MessageDispatcher
from utils.ids import user_id_from_phone_e164
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from config.settings import settings
from repos.user_repo import UserRepository
from repos.auth_repo import AuthRepository

log = logging.getLogger("glitch.router.messaging")
router = APIRouter()


class WelcomeRequest(BaseModel):
    user_id: str
    telegram_chat_id: str


@router.post("/telegram/welcome")
def telegram_welcome(req: WelcomeRequest):
    raise HTTPException(status_code=410, detail="deprecated_use_auth_and_link_flow")

@router.post("/twilio/inbound")
async def twilio_inbound(request: Request):
    # Twilio sends application/x-www-form-urlencoded
    form = await request.form()
    signature = request.headers.get("X-Twilio-Signature", "")

    # Cloud Run forwards proto/host; Twilio signature must validate against the public URL.
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    url = f"{proto}://{host}{request.url.path}"

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    if not validator.validate(url, dict(form), signature):
        resp = MessagingResponse()
        resp.message("Forbidden.")
        return Response(content=str(resp), media_type="application/xml", status_code=403)

    from_phone = str(form.get("From", "")).strip()
    body = str(form.get("Body", "")).strip().upper()

    user_id = user_id_from_phone_e164(from_phone)
    repo = UserRepository()
    user = repo.get(user_id)

    twiml = MessagingResponse()

    if not user:
        twiml.message("We couldn't find your account. Please sign up and complete checkout first.")
        return Response(content=str(twiml), media_type="application/xml")

    # Reverse-OTP login: user texts "LOGIN <code>" to prove phone possession.
    if body.startswith("LOGIN "):
        code = body.replace("LOGIN ", "", 1).strip().upper()
        ch = AuthRepository().get_challenge_by_code(code)
        if not ch:
            twiml.message("Invalid or expired code. Please request a new login code in the app.")
            return Response(content=str(twiml), media_type="application/xml")
        now = int(__import__("time").time())
        exp = int(ch.get("expires_at") or 0)
        if exp <= now or ch.get("consumed_at"):
            twiml.message("Code expired. Please request a new login code in the app.")
            return Response(content=str(twiml), media_type="application/xml")
        if str(ch.get("phone_e164") or "") != from_phone:
            twiml.message("Phone mismatch. Please request a new code from this phone.")
            return Response(content=str(twiml), media_type="application/xml")
        if str(ch.get("user_id") or "") != user_id:
            twiml.message("Account mismatch. Please request a new code.")
            return Response(content=str(twiml), media_type="application/xml")
        AuthRepository().mark_verified(str(ch.get("challenge_id") or ""), from_phone_e164=from_phone)
        flags = AuthRepository().activate_user_if_needed(user_id=str(ch.get("user_id") or ""), phone_e164=from_phone)
        log.info("auth_verified_and_activated", extra={"extra": {"user_id": str(ch.get("user_id") or ""), **(flags or {})}})
        twiml.message("✅ Verified. Return to the app to complete login.")
        return Response(content=str(twiml), media_type="application/xml")

    if body == "YES":
        repo.update(user_id, {"activated_at": datetime.now(timezone.utc).isoformat(), "phone": from_phone})
        twiml.message("✅ Glitch activated. You'll receive alerts only when FDA shortage status changes.")
    else:
        twiml.message("OK")

    return Response(content=str(twiml), media_type="application/xml")

# --- Telegram inbound (reverse-OTP verification) ---
@router.post("/telegram/inbound")
async def telegram_inbound(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")

    msg = (payload or {}).get("message") or {}
    text = str(msg.get("text") or "").strip()
    chat = (msg.get("chat") or {})
    chat_id = chat.get("id")

    if not chat_id:
        raise HTTPException(status_code=400, detail="missing_chat_id")

    parts = text.split()
    if len(parts) < 3 or parts[0].upper() != "LOGIN":
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Send: LOGIN CODE +62812XXXXXXXXX")
        return {"ok": True}

    code = parts[1].strip().upper()
    phone = parts[2].strip()

    user_id = user_id_from_phone_e164(phone)
    if not user_id:
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Invalid phone. Use E.164 like +62812...")
        return {"ok": True}

    ch = AuthRepository().get_challenge_by_code(code)
    if not ch:
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Code not found. Request a new login code in the app.")
        return {"ok": True}

    if str(ch.get("user_id") or "") != user_id:
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Account mismatch. Request a new code.")
        return {"ok": True}
    if str(ch.get("phone_e164") or "") != phone:
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Phone mismatch. Use the same phone used in auth/start.")
        return {"ok": True}

    now = int(time.time())
    exp = int(ch.get("expires_at") or 0)
    if exp <= now:
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Code expired. Request a new login code in the app.")
        return {"ok": True}
    if ch.get("consumed_at"):
        MessageDispatcher().send_telegram(chat_id=str(chat_id), text="Code already used. Request a new login code.")
        return {"ok": True}

    AuthRepository().mark_verified(str(ch.get("challenge_id") or ""), from_phone_e164=phone)
    flags = AuthRepository().activate_user_if_needed(user_id=str(ch.get("user_id") or ""), phone_e164=phone)
    log.info("auth_verified_and_activated", extra={"extra": {"user_id": str(ch.get("user_id") or ""), **(flags or {})}})

    MessageDispatcher().send_telegram(
        chat_id=str(chat_id),
        text=(
            "✅ You're verified.\n\n"
            "Welcome to Glitch.\n"
            "You'll receive alerts only when FDA shortage status changes.\n\n"
            "You’re now securely connected."
        )
    )
    try:
        UserRepository().update(
            user_id=str(ch.get("user_id") or ""),
            data={
                "telegram_chat_id": str(chat_id),
                "telegram_connected_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        log.info("telegram_chat_linked", extra={"extra": {"user_id": str(ch.get("user_id") or ""), "chat_id": str(chat_id)}})
    except Exception:
        log.exception("telegram_chat_link_failed", extra={"extra": {"user_id": str(ch.get("user_id") or ""), "chat_id": str(chat_id)}})
    return {"ok": True}
