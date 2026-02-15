from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from utils.ids import user_id_from_phone_e164
from repos.user_repo import UserRepository
from repos.watchlist_repo import WatchlistRepository
from repos.subscription_repo import SubscriptionRepository
from repos.shortage_repo import ShortageRepository

router = APIRouter()


@router.get("/ui/status")
def ui_status():
    # Safe transparency: do not reveal secrets; only operational config & mode.
    return {
        "ok": True,
        "service": "glitch-api",
        "environment": settings.ENVIRONMENT,
        "payments_enabled": bool(settings.PAYMENTS_ENABLED),
        "fail_closed_limits": bool(settings.FAIL_CLOSED_LIMITS),
        "ingest_mode": settings.INGEST_MODE,
        "openfda_limit": settings.OPENFDA_LIMIT,
        "max_sweep_items": settings.MAX_SWEEP_ITEMS,
    }


class PhoneBody(BaseModel):
    phone_e164: str = Field(..., min_length=6, max_length=32)


@router.post("/ui/user/status")
def ui_user_status(body: PhoneBody):
    user_id = user_id_from_phone_e164(body.phone_e164)
    if not user_id:
        raise HTTPException(status_code=400, detail="invalid_phone")
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
        "watchlist": {
            "count": len(watch),
            "items": watch[:50],
        },
    }


class DiagnosticsBody(BaseModel):
    phone_e164: str = Field(..., min_length=6, max_length=32)
    ndc_digits: str | None = None


@router.post("/ui/user/diagnostics")
def ui_user_diagnostics(body: DiagnosticsBody):
    user_id = user_id_from_phone_e164(body.phone_e164)
    if not user_id:
        raise HTTPException(status_code=400, detail="invalid_phone")
    user = UserRepository().get(user_id) or {}
    sub = SubscriptionRepository().get_by_user(user_id) or {}
    watch = WatchlistRepository().list_ndcs(user_id)

    reasons = []
    if not user:
        reasons.append("user_not_found")
    if settings.PAYMENTS_ENABLED and (not sub or sub.get("status") != "active"):
        reasons.append("subscription_inactive")
    if not user.get("activated_at"):
        reasons.append("not_activated")
    if not user.get("telegram_chat_id") and not user.get("phone"):
        reasons.append("no_delivery_channel")
    if not watch:
        reasons.append("empty_watchlist")

    # NDC-specific diagnostics
    if body.ndc_digits:
        ndc = body.ndc_digits
        s = ShortageRepository().get(ndc)
        if not s:
            reasons.append("ndc_not_in_shortages_store_yet")
        elif not s.get("status"):
            reasons.append("ndc_status_unknown")

    return {"ok": True, "user_id": user_id, "eligible": (len(reasons) == 0), "reasons": reasons}
