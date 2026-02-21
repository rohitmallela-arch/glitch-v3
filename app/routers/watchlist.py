from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config.settings import settings
from repos.shortage_repo import ShortageRepository
from repos.watchlist_repo import WatchlistRepository
from repos.ndc_watchers_repo import NDCWatchersRepository
from billing.entitlements import EntitlementService
from utils.auth import require_session
from ndc.normalizer import normalize_ndc_to_11

router = APIRouter()


class WatchAddRequest(BaseModel):
    ndc: str = Field(..., min_length=5, max_length=64)


@router.get("/watchlist")
def list_watchlist(request: Request):
    user_id, _phone = require_session(request)
    EntitlementService().require_active(user_id)
    wl = WatchlistRepository()
    return {"ok": True, "items": wl.list_ndcs(user_id)}


@router.post("/watchlist/add")
def add_watch(request: Request, req: WatchAddRequest):
    user_id, _phone = require_session(request)
    EntitlementService().require_active(user_id)

    wl = WatchlistRepository()
    current = wl.count(user_id)
    if settings.FAIL_CLOSED_LIMITS and current >= settings.MAX_WATCHLIST_ITEMS:
        raise HTTPException(status_code=403, detail="watchlist_limit_reached")

    ndc11 = normalize_ndc_to_11(req.ndc)
    if not ndc11:
        raise HTTPException(status_code=400, detail="invalid_ndc")

    s = ShortageRepository().get(ndc11) or {}
    wl.add(
        user_id,
        ndc11,
        {
            "added_at": "now",
            "brand_name": s.get("brand_name", ""),
            "generic_name": s.get("generic_name", ""),
        },
    )
    NDCWatchersRepository().add_watcher(ndc11, user_id)
    return {"ok": True, "user_id": user_id, "ndc_digits": ndc11}


@router.delete("/watchlist/remove")
def remove_watch(request: Request, ndc: str):
    user_id, _phone = require_session(request)
    EntitlementService().require_active(user_id)

    ndc11 = normalize_ndc_to_11(ndc)
    if not ndc11:
        raise HTTPException(status_code=400, detail="invalid_ndc")

    WatchlistRepository().remove(user_id, ndc11)
    return {"ok": True, "removed": ndc11}
