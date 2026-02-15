from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from billing.entitlements import EntitlementService
from config.settings import settings
from ndc.normalizer import normalize_ndc_to_11
from repos.watchlist_repo import WatchlistRepository
from repos.ndc_watchers_repo import NDCWatchersRepository
from utils.ids import user_id_from_phone_e164
from repos.shortage_repo import ShortageRepository

router = APIRouter()


class WatchAddRequest(BaseModel):
    user_id: str | None = Field(default=None, min_length=3, max_length=128)
    phone_e164: str | None = Field(default=None, min_length=6, max_length=32)
    ndc: str = Field(..., min_length=5, max_length=64)


@router.get("/watchlist")
def list_watchlist(user_id: str):
    EntitlementService().require_active(user_id)
    wl = WatchlistRepository()
    return {"ok": True, "items": wl.list_ndcs(user_id)}


@router.post("/watchlist/add")
def add_watch(req: WatchAddRequest):
    user_id = req.user_id or (user_id_from_phone_e164(req.phone_e164 or "") if req.phone_e164 else "")
    if not user_id:
        raise HTTPException(status_code=400, detail="missing_user_id")
    EntitlementService().require_active(user_id)

    wl = WatchlistRepository()
    current = wl.count(user_id)
    if settings.FAIL_CLOSED_LIMITS and current >= settings.MAX_WATCHLIST_ITEMS:
        raise HTTPException(status_code=403, detail="watchlist_limit_reached")

    ndc11 = normalize_ndc_to_11(req.ndc)
    if not ndc11:
        raise HTTPException(status_code=400, detail="invalid_ndc")

    # enrich from shortages if available
    s = ShortageRepository().get(ndc11) or {}
    wl.add(user_id, ndc11, {"added_at": "now", "brand_name": s.get("brand_name",""), "generic_name": s.get("generic_name","")})
    NDCWatchersRepository().add_watcher(ndc11, user_id)
    return {"ok": True, "user_id": user_id, "ndc_digits": ndc11}


@router.delete("/watchlist/remove")
def remove_watch(user_id: str, ndc: str):
    EntitlementService().require_active(user_id)
    ndc11 = normalize_ndc_to_11(ndc)
    WatchlistRepository().remove(user_id, ndc11)
    return {"ok": True, "removed": ndc11}
