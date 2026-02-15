from __future__ import annotations

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

log = logging.getLogger("glitch.router.messaging")
router = APIRouter()


class WelcomeRequest(BaseModel):
    user_id: str
    telegram_chat_id: str


@router.post("/telegram/welcome")
def telegram_welcome(req: WelcomeRequest):
    user = UserRepository().get(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    UserRepository().update(req.user_id, {"telegram_chat_id": req.telegram_chat_id})
    resp = MessageDispatcher().send_telegram(chat_id=req.telegram_chat_id, text="<b>Welcome to Glitch</b>\nYou're set up. We'll stay silent unless something changes.")
    return {"ok": True, "resp": resp}


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

    if body == "YES":
        repo.update(user_id, {"activated_at": datetime.now(timezone.utc).isoformat(), "phone": from_phone})
        twiml.message("✅ Glitch activated. You'll receive alerts only when FDA shortage status changes.")
    else:
        twiml.message("OK")

    return Response(content=str(twiml), media_type="application/xml")
