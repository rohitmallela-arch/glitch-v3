from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from ingest.openfda_client import fetch_shortages_page
from ingest.delta_engine import snapshot_hash, variant_key
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

    # Group upstream records by NDC11 to prevent variant flip-flop overwrites.
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        package_ndc = r.get("package_ndc") or r.get("package_ndc11") or r.get("ndc") or ""
        ndc11 = normalize_ndc_to_11(package_ndc)
        if not ndc11:
            continue
        grouped.setdefault(ndc11, []).append(r)

    for ndc11, recs in grouped.items():
        existing = shortage_repo.get(ndc11) or {}

        # Backward-compatible read: older docs only had snapshot_hash.
        existing_head_hash = existing.get("headline_snapshot_hash") or existing.get("snapshot_hash")

        vkey_to_record: Dict[str, Dict[str, Any]] = {}
        vkey_to_hash: Dict[str, str] = {}

        # Upsert all variants for this ndc11.
        for r in recs:
            vkey = variant_key(r)
            vhash = snapshot_hash(r)
            vkey_to_record[vkey] = r
            vkey_to_hash[vkey] = vhash

            variant_doc = {
                "ndc_digits": ndc11,
                "variant_key": vkey,
                "status": r.get("status") or "",
                "last_updated": r.get("last_updated") or "",
                "shortage_start_date": r.get("shortage_start_date") or "",
                "shortage_end_date": r.get("shortage_end_date") or "",
                "presentation": r.get("presentation") or "",
                "reason": r.get("reason") or "",
                "resolution": r.get("resolution") or "",
                "source": "openfda",
                "snapshot_hash": vhash,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            shortage_repo.upsert_variant(ndc11, vkey, variant_doc)
            processed += 1  # preserve historical meaning: records processed

        # Deterministic headline: lexicographically smallest variant_key.
        headline_vkey = sorted(vkey_to_hash.keys())[0]
        headline_hash = vkey_to_hash[headline_vkey]
        headline_rec = vkey_to_record[headline_vkey]

        is_changed = (existing_head_hash is None) or (existing_head_hash != headline_hash)

        # Resolve naming once for rollup (using deterministic headline record as fallback).
        resolved = resolver.resolve_with_fallback(ndc11, fallback=headline_rec)

        # Parent rollup doc (backward compatible): keep snapshot_hash as headline hash.
        doc = {
            "ndc_digits": ndc11,
            "source": "openfda",
            "variants_count": len(vkey_to_hash),
            "headline_variant_key": headline_vkey,
            "headline_snapshot_hash": headline_hash,

            # Back-compat for existing readers/UI:
            "snapshot_hash": headline_hash,

            # Headline fields (for UI/alerts)
            "status": headline_rec.get("status") or "",
            "last_updated": headline_rec.get("last_updated") or "",
            "shortage_start_date": headline_rec.get("shortage_start_date") or "",
            "shortage_end_date": headline_rec.get("shortage_end_date") or "",
            "presentation": headline_rec.get("presentation") or "",
            "reason": headline_rec.get("reason") or "",
            "resolution": headline_rec.get("resolution") or "",

            "brand_name": resolved.get("brand_name") or "",
            "generic_name": resolved.get("generic_name") or "",
            "manufacturer": resolved.get("manufacturer") or "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        shortage_repo.upsert(ndc11, doc)

        if is_changed:
            changed += 1

            # Fan out alerts only during delta runs (once per NDC11 rollup change).
            if mode == "delta":
                watchers_repo = NDCWatchersRepository()
                users_repo = UserRepository()
                subs_repo = SubscriptionRepository()
                rate_repo = RateLimitRepository()
                alert_dispatcher = AlertDispatcher()

                old_status = existing.get("status") if existing else None
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

    # Report real baseline state (not just whether this run was "baseline")
    baseline_completed_out = bool(state_repo.get_state().get("baseline_completed", False))
    return {"ok": True, "processed": processed, "changed": changed, "baseline_completed": baseline_completed_out}
