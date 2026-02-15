from __future__ import annotations

import stripe
from config.settings import settings

stripe.api_key = settings.STRIPE_API_KEY


def create_checkout_session(user_id: str, phone_e164: str | None = None, watchlist_ndcs: str | None = None) -> dict:
    if not settings.STRIPE_PRICE_ID:
        raise RuntimeError("STRIPE_PRICE_ID not configured")
    if not settings.APP_BASE_URL:
        # To keep it deterministic, require explicit base URL.
        raise RuntimeError("APP_BASE_URL not configured (needed for success/cancel URLs)")

    success_url = f"{settings.APP_BASE_URL}/ui/checkout_success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.APP_BASE_URL}/ui/checkout_cancel"

    metadata = {}
    if phone_e164:
        metadata["phone_e164"] = phone_e164
    if watchlist_ndcs:
        metadata["watchlist_ndcs"] = watchlist_ndcs

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=user_id,
        metadata=metadata,
    )
    return session
