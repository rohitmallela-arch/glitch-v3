from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from ingest.openfda_client import fetch_shortages_page
from ingest.delta_engine import snapshot_hash
from ndc.resolver import NDCResolver
from ndc.normalizer import normalize_ndc_to_11
from repos.ingest_state_repo import IngestStateRepository
from repos.shortage_repo import ShortageRepository
from repos.ndc_watchers_repo import NDCWatchersRepository
from repos.user_repo import UserRepository
from repos.subscription_repo import SubscriptionRepository
from repos.rate_limit_repo import RateLimitRepository, utc_day_key
from alerts.dispatch import AlertDispatcher

log = logging.getLogger("glitch.ingest.sweeper")


def sweep_all_shortages() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    limit = settings.OPENFDA_LIMIT
    max_items = settings.MAX_SWEEP_ITEMS
    all_results: List[Dict[str, Any]] = []
    skip = 0
    meta_last = {}

    while True:
        page, meta = fetch_shortages_page(skip=skip, limit=limit)
        meta_last = meta
        if not page:
            break
        all_results.extend(page)
        if len(all_results) >= max_items:
            # Fail-closed
            raise RuntimeError(f"max_sweep_items_exceeded: fetched={len(all_results)} cap={max_items}")
        skip += limit

    return all_results, {"meta": meta_last, "total_fetched": len(all_results)}


def upsert_and_detect_changes(records: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
    state_repo = IngestStateRepository()
    shortage_repo = ShortageRepository()
    resolver = NDCResolver()

    state = state_repo.get_state()
    baseline_completed = bool(state.get("baseline_completed", False))

    if mode == "delta" and not baseline_completed:
        # Fail-closed: do not alert, do not process as delta before baseline
        return {"ok": False, "error": "baseline_not_completed", "processed": 0, "changed": 0}

    changed = 0
    processed = 0

    for r in records:
        package_ndc = r.get("package_ndc") or r.get("package_ndc11") or r.get("ndc") or ""
        ndc11 = normalize_ndc_to_11(package_ndc)
        if not ndc11:
            continue

        existing = shortage_repo.get(ndc11)
        existing_hash = (existing or {}).get("snapshot_hash")

        new_hash = snapshot_hash(r)
        is_changed = (existing_hash is None) or (existing_hash != new_hash)

        # Resolve naming
        resolved = resolver.resolve_with_fallback(ndc11, fallback=r)

        # Normalize stored shortage doc
        doc = {
            "ndc_digits": ndc11,
            "status": r.get("status") or "",
            "last_updated": r.get("last_updated") or "",
            "shortage_start_date": r.get("shortage_start_date") or "",
            "shortage_end_date": r.get("shortage_end_date") or "",
            "presentation": r.get("presentation") or "",
            "reason": r.get("reason") or "",
            "resolution": r.get("resolution") or "",
            "brand_name": resolved.get("brand_name") or "",
            "generic_name": resolved.get("generic_name") or "",
            "manufacturer": resolved.get("manufacturer") or "",
            "source": "openfda",
            "snapshot_hash": new_hash,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        shortage_repo.upsert(ndc11, doc)
        processed += 1
        if is_changed:
            changed += 1

            # Fan out alerts only during delta runs.
            if mode == "delta":
                watchers_repo = NDCWatchersRepository()
                users_repo = UserRepository()
                subs_repo = SubscriptionRepository()
                rate_repo = RateLimitRepository()
                alert_dispatcher = AlertDispatcher()

                old_status = (existing or {}).get("status") if existing else None
                new_status = doc.get("status")

                for watcher_user_id in watchers_repo.iter_watchers(ndc11):
                    # Entitlement + activation checks (fail-closed)
                    sub = subs_repo.get_by_user(watcher_user_id) or {}
                    if settings.PAYMENTS_ENABLED and sub.get("status") != "active":
                        continue
                    user = users_repo.get(watcher_user_id) or {}
                    if not user.get("activated_at"):
                        continue

                    chat_id = user.get("telegram_chat_id")
                    if not chat_id:
                        continue

                    # Rate limit reservation (transactional)
                    day_key = utc_day_key()
                    tx = rate_repo.db.transaction()
                    ok, reason = rate_repo.reserve_quota(tx, watcher_user_id, ndc11, day_key, settings.MAX_ALERTS_PER_DAY, settings.MAX_ALERTS_PER_NDC_PER_DAY)
                    if not ok:
                        log.info("rate_limit_skip", extra={"extra": {"user_id": watcher_user_id, "ndc": ndc11, "reason": reason}})
                        continue

                    payload = {
                        "ndc_digits": ndc11,
                        "brand_name": doc.get("brand_name"),
                        "generic_name": doc.get("generic_name"),
                        "manufacturer": doc.get("manufacturer"),
                        "old_status": old_status,
                        "new_status": new_status,
                        "last_updated": doc.get("last_updated"),
                    }
                    alert_dispatcher.dispatch_telegram(watcher_user_id, chat_id, payload)

    if mode == "baseline":
        state_repo.set_baseline_completed()

    state_repo.update_sweep_metrics({
        "last_sweep_started_at": datetime.now(timezone.utc).isoformat(),
        "last_sweep_mode": mode,
        "last_sweep_total_processed": processed,
        "last_sweep_changed": changed,
        "last_sweep_completed_at": datetime.now(timezone.utc).isoformat(),
    })

    return {"ok": True, "processed": processed, "changed": changed, "baseline_completed": (mode=="baseline")}
