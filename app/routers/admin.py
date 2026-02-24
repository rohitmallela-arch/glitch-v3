from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from config.settings import settings
from digest.weekly import run_weekly_digest_for_user
from ingest.shortage_sweeper import sweep_all_shortages, upsert_and_detect_changes
from messaging.dispatcher import MessageDispatcher
from repos.subscription_repo import SubscriptionRepository
from repos.user_repo import UserRepository
from repos.telegram_chat_index_repo import TelegramChatIndexRepository
from security.operator_auth import OperatorClaims, verify_operator_request

router = APIRouter()
log = logging.getLogger("glitch.routers.admin")


class TestAlertRequest(BaseModel):
    user_id: str


@router.get("/whoami")
def whoami(request: Request):
    claims = verify_operator_request(request)
    return {"ok": True, "claims": {"sub": claims.get("sub"), "email": claims.get("email"), "aud": claims.get("aud")}}


@router.post("/run_delta_now")
def run_delta_now(request: Request):
    verify_operator_request(request)
    try:
        recs, meta = sweep_all_shortages()
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "fetch", "mode": "delta", "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    try:
        result = upsert_and_detect_changes(recs, mode="delta")
        changed = int((result or {}).get("changed", 0) or 0)
        threshold = int(getattr(settings, "DELTA_MAX_ALLOWED_CHANGES", 200) or 200)
        if changed > threshold:
            log.error(
                "delta_anomaly_guard_triggered",
                extra={"extra": {
                    "event": "delta_anomaly_guard_triggered",
                    "mode": "delta",
                    "changed": changed,
                    "threshold": threshold,
                }},
            )
            raise HTTPException(status_code=503, detail="delta_anomaly_guard_triggered")
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "upsert", "mode": "delta", "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    return {"ok": True, "meta": meta, "result": result}


@router.post("/run_baseline_now")
def run_baseline_now(request: Request):
    verify_operator_request(request)
    try:
        recs, meta = sweep_all_shortages()
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "fetch", "mode": "baseline", "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    try:
        result = upsert_and_detect_changes(recs, mode="baseline")
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "upsert", "mode": "baseline", "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    return {"ok": True, "meta": meta, "result": result}


@router.post("/set_ingest_mode")
def set_ingest_mode(request: Request, mode: str):
    verify_operator_request(request)
    # runtime env not mutable; this is informational endpoint
    return {
        "ok": True,
        "current_ingest_mode": settings.INGEST_MODE,
        "requested": mode,
        "note": "Set via env var at deploy time.",
    }


@router.post("/weekly_recap_run")
def weekly_recap_run(request: Request):
    verify_operator_request(request)
    users_repo = UserRepository()
    subs_repo = SubscriptionRepository()
    sent = 0
    scanned = 0

    # Stream all users; for MVP scale (<=1000) this is acceptable.
    for snap in users_repo.db.collection("users").stream():
        scanned += 1
        user_id = snap.id
        user = snap.to_dict() or {}
        chat_id = user.get("telegram_chat_id")
        if not chat_id:
            continue
        if settings.PAYMENTS_ENABLED:
            sub = subs_repo.get_by_user(user_id) or {}
            if sub.get("status") != "active":
                continue
        if not user.get("activated_at"):
            continue
        out = run_weekly_digest_for_user(user_id, chat_id)
        if out.get("sent"):
            sent += 1

    return {"ok": True, "scanned_users": scanned, "sent": sent}


@router.post("/test_alert")
def test_alert(request: Request, body: TestAlertRequest, claims: OperatorClaims = OperatorClaims):
    """
    Deterministic forced Telegram test.
    - Operator auth required (OIDC)
    - Input: { "user_id": "u_..." }
    - Reuses existing MessageDispatcher Telegram sender
    - Does not touch delta logic
    """
    # Ensure operator auth is enforced even if dependency injection changes later.
    verify_operator_request(request)

    user_id = body.user_id.strip()
    users_repo = UserRepository()

    user = users_repo.get(user_id)
    if not user:
        return {"ok": False, "error": "user_not_found", "user_id": user_id}

    chat_id = user.get("telegram_chat_id")
    if not chat_id:
        return {"ok": False, "error": "telegram_not_connected", "user_id": user_id}

    msg = f"✅ <b>Glitch test alert</b>\nuser_id={user_id}\nIf you see this, Telegram delivery is working."
    resp = MessageDispatcher().send_telegram(chat_id=str(chat_id), text=msg)

    log.info(
        "admin_test_alert_sent",
        extra={
            "extra": {
                "user_id": user_id,
                "chat_id": str(chat_id),
                "telegram_ok": bool(resp.get("ok", False)),
                "operator_sub": (claims.get("sub") if isinstance(claims, dict) else None),
                "operator_email": (claims.get("email") if isinstance(claims, dict) else None),
            }
        },
    )

    return {
        "ok": True,
        "user_id": user_id,
        "telegram_chat_id": str(chat_id),
        "telegram_response_ok": bool(resp.get("ok", False)),
        "telegram_response": resp,
    }


class TestShortageAlertRequest(BaseModel):
    user_id: str
    ndc_digits: str


@router.post("/test_shortage_alert")
def test_shortage_alert(request: Request, body: TestShortageAlertRequest):
    """
    Deterministic forced shortage-change-style Telegram alert (uses alerts.formatter).
    - Operator auth required (OIDC)
    - Input: { "user_id": "u_...", "ndc_digits": "00002431208" }
    - Fetches shortages/{ndc11} rollup doc and uses presentation/generic/brand fields
    - Sends via AlertDispatcher (formatter path), so we can verify "name + hyphenated NDC"
    """
    verify_operator_request(request)

    user_id = (body.user_id or "").strip()
    ndc11 = (body.ndc_digits or "").strip()

    users_repo = UserRepository()
    user = users_repo.get(user_id)
    if not user:
        return {"ok": False, "error": "user_not_found", "user_id": user_id}

    chat_id = user.get("telegram_chat_id")
    if not chat_id:
        return {"ok": False, "error": "telegram_not_connected", "user_id": user_id}

    from repos.shortage_repo import ShortageRepository
    from alerts.dispatch import AlertDispatcher

    shortage = ShortageRepository().get(ndc11) or {}
    if not shortage:
        return {"ok": False, "error": "shortage_not_found", "ndc_digits": ndc11}

    # Use real shortage fields; fake a status transition deterministically.
    new_status = (shortage.get("status") or "unknown").strip() or "unknown"
    old_status = "unknown" if new_status == "unknown" else "previous_status"

    payload = {
        "ndc_digits": ndc11,
        "brand_name": shortage.get("brand_name") or "",
        "generic_name": shortage.get("generic_name") or "",
        "manufacturer": shortage.get("manufacturer") or "",
        "presentation": shortage.get("presentation") or "",
        "old_status": old_status,
        "new_status": new_status,
        "last_updated": shortage.get("last_updated") or "",
    }

    resp = AlertDispatcher().dispatch_telegram(user_id=user_id, chat_id=str(chat_id), payload=payload, sweep_id="admin_test_shortage_alert")

    log.info(
        "admin_test_shortage_alert_sent",
        extra={"extra": {"event": "admin_test_shortage_alert_sent", "user_id": user_id, "ndc_digits": ndc11, "telegram_ok": bool(resp.get("ok", False))}},
    )

    return {"ok": True, "user_id": user_id, "ndc_digits": ndc11, "telegram_response_ok": bool(resp.get("ok", False)), "telegram_response": resp}


@router.post("/telegram_link_test")
def admin_telegram_link_test(body: dict, request: Request):
    # Operator-only: deterministic invariant test harness.
    verify_operator_request(request)

    chat_id = str((body or {}).get("chat_id") or "").strip()
    user_id = str((body or {}).get("user_id") or "").strip()
    if not chat_id or not user_id:
        raise HTTPException(status_code=400, detail="chat_id and user_id required")

    idx = TelegramChatIndexRepository()
    existing = idx.get(chat_id) or {}
    existing_uid = str(existing.get("canonical_user_id") or "").strip()

    if existing_uid and existing_uid != user_id:
        return {"ok": True, "linked": False, "error": "telegram_chat_already_linked", "existing_user_id": existing_uid}

    idx.set(chat_id, user_id)
    return {"ok": True, "linked": True, "canonical_user_id": user_id}
