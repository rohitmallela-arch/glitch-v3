from __future__ import annotations

from fastapi import APIRouter, Request
from security.operator_auth import verify_operator_request, OperatorClaims
from ingest.shortage_sweeper import sweep_all_shortages, upsert_and_detect_changes
from config.settings import settings

router = APIRouter()

from digest.weekly import run_weekly_digest_for_user
from repos.user_repo import UserRepository
from repos.subscription_repo import SubscriptionRepository
from config.settings import settings



@router.get("/whoami")
def whoami(request: Request):
    claims = verify_operator_request(request)
    return {"ok": True, "claims": {"sub": claims.get("sub"), "email": claims.get("email"), "aud": claims.get("aud")}}


@router.post("/run_delta_now")
def run_delta_now(request: Request):
    verify_operator_request(request)
    recs, meta = sweep_all_shortages()
    result = upsert_and_detect_changes(recs, mode="delta")
    return {"ok": True, "meta": meta, "result": result}


@router.post("/run_baseline_now")
def run_baseline_now(request: Request):
    verify_operator_request(request)
    recs, meta = sweep_all_shortages()
    result = upsert_and_detect_changes(recs, mode="baseline")
    return {"ok": True, "meta": meta, "result": result}


@router.post("/set_ingest_mode")
def set_ingest_mode(request: Request, mode: str):
    verify_operator_request(request)
    # runtime env not mutable; this is informational endpoint
    return {"ok": True, "current_ingest_mode": settings.INGEST_MODE, "requested": mode, "note": "Set via env var at deploy time."}


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
