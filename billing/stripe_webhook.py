from __future__ import annotations

import logging
from typing import Any, Dict

import stripe
from fastapi import Header, HTTPException, Request

from config.settings import settings
from repos.subscription_repo import SubscriptionRepository
from models.schema import COL_SUBSCRIPTIONS
from repos.user_repo import UserRepository
from repos.watchlist_repo import WatchlistRepository
from repos.ndc_watchers_repo import NDCWatchersRepository
from utils.ids import user_id_from_phone_e164
from ndc.normalizer import normalize_ndc_to_11

log = logging.getLogger("glitch.stripe")


class StripeWebhookHandler:
    def __init__(self):
        stripe.api_key = settings.STRIPE_API_KEY
        self.repo = SubscriptionRepository()

    async def handle(self, request: Request, stripe_signature: str | None) -> Dict[str, Any]:
        payload = await request.body()
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="missing_stripe_signature")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except Exception as e:
            log.warning("stripe signature verify failed", extra={"extra": {"error": str(e)}})
            raise HTTPException(status_code=400, detail="invalid_signature")

        event_id = event.get("id")
        event_type = event.get("type")

        # Idempotency: store last processed event id in subscription doc (merge-safe)
        # (In production, you might use a dedicated processed_events collection; this is sufficient for single-plan MVP.)
        obj = event.get("data", {}).get("object", {}) or {}

        # Determine user_id
        user_id = None
        if event_type == "checkout.session.completed":
            user_id = obj.get("client_reference_id")
            sub_id = obj.get("subscription")
            cust_id = obj.get("customer")
            if user_id:
                # Create user if absent (phone-based ID may be used)
                md = obj.get("metadata") or {}
                phone = md.get("phone_e164") or ""
                if phone and not user_id.startswith("u_"):
                    # prefer deterministic phone-based ID if provided
                    user_id = user_id_from_phone_e164(phone) or user_id
                UserRepository().create_if_absent(user_id, {"phone": phone, "email": ""})

                # If watchlist metadata provided, populate watchlist and watcher index
                wl_raw = (md.get("watchlist_ndcs") or "").strip()
                if wl_raw:
                    wl_repo = WatchlistRepository()
                    watchers = NDCWatchersRepository()
                    for part in [p.strip() for p in wl_raw.split(",") if p.strip()]:
                        ndc11 = normalize_ndc_to_11(part)
                        if not ndc11:
                            continue
                        wl_repo.add(user_id, ndc11, {"added_via": "stripe_metadata"})
                        watchers.add_watcher(ndc11, user_id)

                self.repo.upsert(user_id, {
                    "status": "active",
                    "stripe_subscription_id": sub_id,
                    "stripe_customer_id": cust_id,
                    "last_event_id": event_id,
                    "last_event_type": event_type,
                })
        elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
            # Fail-closed: mark subscription inactive
            sub_id = obj.get("id") or obj.get("subscription")
            cust_id = obj.get("customer")

            # MVP: locate user by scanning subscriptions collection
            # (Scale path: add subscription_id -> user_id index.)
            query = (
                self.repo.db.collection(COL_SUBSCRIPTIONS)
                .where("stripe_subscription_id", "==", sub_id)
                .limit(1)
            )
            snaps = list(query.stream())

            if not snaps and cust_id:
                query = (
                    self.repo.db.collection(COL_SUBSCRIPTIONS)
                    .where("stripe_customer_id", "==", cust_id)
                    .limit(1)
                )
                snaps = list(query.stream())

            if snaps:
                snap = snaps[0]
                user_id = snap.id
                self.repo.upsert(user_id, {
                    "status": "inactive",
                    "last_event_id": event_id,
                    "last_event_type": event_type,
                })
                log.info("subscription marked inactive", extra={"extra": {"user_id": user_id, "event_type": event_type}})
            else:
                log.warning("subscription lifecycle event with no matching user", extra={"extra": {"stripe_subscription_id": sub_id, "customer": cust_id, "event_type": event_type}})

        return {"ok": True, "event_type": event_type, "event_id": event_id}
# deploy-1771671709
