from __future__ import annotations

import logging
import time
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config.settings import settings
from utils.ids import user_id_from_phone_e164
from repos.user_repo import UserRepository
from repos.subscription_repo import SubscriptionRepository
from repos.watchlist_repo import WatchlistRepository
from repos.auth_repo import AuthRepository
from utils.auth import mint_bearer_token, require_session

log = logging.getLogger("glitch.router.auth")
router = APIRouter()

CHALLENGE_TTL_SEC = 10 * 60
SESSION_TTL_SEC = 7 * 24 * 60 * 60  # 7 days


class AuthStartBody(BaseModel):
    phone_e164: str = Field(..., min_length=6, max_length=32)


@router.post("/ui/auth/start")
def ui_auth_start(body: AuthStartBody):
    phone = body.phone_e164.strip()
    user_id = user_id_from_phone_e164(phone)
    if not user_id:
        raise HTTPException(status_code=400, detail="invalid_phone")

    user = UserRepository().get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")

    # Code is short human friendly; challenge_id is deterministic hash of code for lookup on inbound.
    code = "GL-" + "".join([c for c in __import__("secrets").token_urlsafe(6).upper() if c.isalnum()][:6])
    try:
        AuthRepository().create_challenge(phone_e164=phone, user_id=user_id, code=code, ttl_sec=CHALLENGE_TTL_SEC)
    except ValueError as e:
        reason = str(e) or "rate_limited"
        log.info("auth_rate_limited", extra={"extra": {"user_id": user_id, "reason": reason}})
        raise HTTPException(status_code=429, detail=reason)

    instr = f"Send Telegram message to the bot: LOGIN {code} {phone} (within {CHALLENGE_TTL_SEC//60} minutes)."
    log.info("auth_start_issued", extra={"extra": {"user_id": user_id}})

    return {"ok": True, "user_id": user_id, "code": code, "expires_in_sec": CHALLENGE_TTL_SEC, "instructions": instr}


class AuthCompleteBody(BaseModel):
    phone_e164: str = Field(..., min_length=6, max_length=32)
    code: str = Field(..., min_length=3, max_length=32)


@router.post("/ui/auth/complete")
def ui_auth_complete(body: AuthCompleteBody):
    phone = body.phone_e164.strip()
    code = body.code.strip().upper()

    user_id = user_id_from_phone_e164(phone)
    if not user_id:
        raise HTTPException(status_code=400, detail="invalid_phone")

    ch = AuthRepository().get_challenge_by_code(code)
    if not ch:
        raise HTTPException(status_code=404, detail="challenge_not_found")

    # Fail-closed checks
    if str(ch.get("user_id") or "") != user_id:
        raise HTTPException(status_code=403, detail="challenge_user_mismatch")
    if str(ch.get("phone_e164") or "") != phone:
        raise HTTPException(status_code=403, detail="challenge_phone_mismatch")

    now = int(time.time())
    exp = int(ch.get("expires_at") or 0)
    if exp <= now:
        raise HTTPException(status_code=403, detail="challenge_expired")
    if ch.get("consumed_at"):
        raise HTTPException(status_code=403, detail="challenge_consumed")
    if not ch.get("verified_at"):
        raise HTTPException(status_code=403, detail="challenge_not_verified_yet")

    # Mint bearer session
    token = mint_bearer_token()
    AuthRepository().create_session(user_id=user_id, phone_e164=phone, token=token, ttl_sec=SESSION_TTL_SEC)
    AuthRepository().mark_consumed(str(ch.get("challenge_id") or ""))

    log.info("auth_session_issued", extra={"extra": {"user_id": user_id}})
    return {"ok": True, "user_id": user_id, "token": token, "expires_in_sec": SESSION_TTL_SEC}


@router.get("/ui/me")
def ui_me(request: Request):
    user_id, _phone = require_session(request)

    user = UserRepository().get(user_id) or {}
    sub = SubscriptionRepository().get_by_user(user_id) or {}
    watch = WatchlistRepository().list_ndcs(user_id)

    return {
        "ok": True,
        "user_id": user_id,
        "user": {
            "has_user": bool(user),
            "telegram_connected": bool(user.get("telegram_chat_id")),
            "activated": bool(user.get("activated_at")),
        },
        "subscription": {
            "has_subscription": bool(sub),
            "status": sub.get("status", "none"),
        },
        "watchlist": {"count": len(watch), "items": watch[:50]},
        "subscription_required": not (sub and sub.get("status") == "active"),
    }
