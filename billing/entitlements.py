from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import HTTPException

from config.settings import settings
from repos.subscription_repo import SubscriptionRepository


class SubscriptionRequired(Exception):
    def __init__(self, upgrade_url: str = "/api/checkout_session", status: str = "inactive"):
        super().__init__("subscription_required")
        self.upgrade_url = upgrade_url
        self.status = status


class EntitlementService:
    def __init__(self, repo: Optional[SubscriptionRepository] = None):
        self.repo = repo or SubscriptionRepository()

    def require_active(self, user_id: str) -> Dict[str, Any]:
        if not settings.PAYMENTS_ENABLED:
            # When payments disabled, allow everything (useful for pilots).
            return {"status": "bypassed", "user_id": user_id}

        sub = self.repo.get_by_user(user_id)
        if not sub:
            raise HTTPException(status_code=402, detail="subscription_required")
        if sub.get("status") != "active":
            raise HTTPException(status_code=402, detail=f"subscription_not_active:{sub.get('status')}")
        return sub
