from __future__ import annotations

from typing import Optional, Tuple
import secrets
import time

from fastapi import HTTPException, Request

from repos.auth_repo import AuthRepository


def mint_bearer_token() -> str:
    # 32 bytes -> urlsafe; deterministic enough, no local python needed (runtime only)
    return secrets.token_urlsafe(32)


def parse_bearer_token(request: Request) -> str:
    h = request.headers.get("Authorization", "").strip()
    if not h:
        raise HTTPException(status_code=401, detail="missing_auth")
    parts = h.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="invalid_auth_header")
    return parts[1].strip()


def require_session(request: Request) -> Tuple[str, str]:
    """
    Returns (user_id, phone_e164) for a valid non-expired, non-revoked session.
    """
    token = parse_bearer_token(request)
    s = AuthRepository().get_session_by_token(token)
    if not s:
        raise HTTPException(status_code=401, detail="invalid_session")
    if s.get("revoked_at"):
        raise HTTPException(status_code=401, detail="revoked_session")
    now = int(time.time())
    exp = int(s.get("expires_at") or 0)
    if exp <= now:
        raise HTTPException(status_code=401, detail="expired_session")
    return (str(s.get("user_id") or ""), str(s.get("phone_e164") or ""))
