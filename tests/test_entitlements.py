import pytest
from fastapi import HTTPException
from billing.entitlements import EntitlementService

class FakeRepo:
    def __init__(self, sub):
        self.sub = sub
    def get_by_user(self, user_id):
        return self.sub

def test_entitlement_requires_active():
    svc = EntitlementService(repo=FakeRepo({"status": "canceled"}))
    with pytest.raises(HTTPException):
        svc.require_active("u1")
