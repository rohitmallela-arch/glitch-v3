from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from repos.user_repo import UserRepository

router = APIRouter()


class SignupRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=128)
    email: str | None = None
    phone: str | None = None


@router.post("/signup")
def signup(req: SignupRequest):
    repo = UserRepository()
    user = repo.create_if_absent(req.user_id, {"email": req.email or "", "phone": req.phone or ""})
    return {"ok": True, "user": user}
