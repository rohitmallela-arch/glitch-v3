from __future__ import annotations

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from billing.stripe_service import create_checkout_session
from billing.stripe_webhook import StripeWebhookHandler

router = APIRouter()


class CheckoutRequest(BaseModel):
    user_id: str | None = Field(default=None, min_length=3, max_length=128)
    phone_e164: str | None = None
    watchlist_ndcs: str | None = None


@router.post("/checkout_session")
def checkout_session(req: CheckoutRequest):
    from utils.ids import user_id_from_phone_e164
    user_id = req.user_id or (user_id_from_phone_e164(req.phone_e164 or "") if req.phone_e164 else "")
    if not user_id:
        raise ValueError("missing_user_id")
    session = create_checkout_session(user_id=user_id, phone_e164=req.phone_e164, watchlist_ndcs=req.watchlist_ndcs)
    return {"ok": True, "checkout_url": session.get("url"), "id": session.get("id")}


@router.post("/stripe_webhook")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(default=None, alias="Stripe-Signature")):
    handler = StripeWebhookHandler()
    result = await handler.handle(request, stripe_signature)
    return result
