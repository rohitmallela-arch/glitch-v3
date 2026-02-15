from __future__ import annotations

import logging
from typing import Optional, Set

from fastapi import HTTPException, Request
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config.settings import settings

log = logging.getLogger("glitch.operator_auth")


def _split_csv(v: str) -> Set[str]:
    return {x.strip() for x in (v or "").split(",") if x.strip()}


def verify_operator_request(request: Request) -> dict:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer_token")

    token = auth.split(" ", 1)[1].strip()
    audience = settings.OPERATOR_AUTH_AUDIENCE
    if not audience:
        # Fail closed: require explicit audience to be configured in prod
        raise HTTPException(status_code=500, detail="operator_auth_audience_not_configured")

    try:
        claims = id_token.verify_oauth2_token(token, google_requests.Request(), audience=audience)
    except Exception as e:
        log.warning("operator_auth verify failed", extra={"extra": {"error": str(e)}})
        raise HTTPException(status_code=401, detail="invalid_operator_token")

    allowed_subs = _split_csv(settings.OPERATOR_INVOKER_SUBS)
    allowed_emails = _split_csv(settings.OPERATOR_INVOKER_EMAILS)

    sub = claims.get("sub", "")
    email = claims.get("email", "")

    if allowed_subs and sub not in allowed_subs:
        raise HTTPException(status_code=403, detail="operator_sub_not_allowed")
    if allowed_emails and email and email not in allowed_emails:
        raise HTTPException(status_code=403, detail="operator_email_not_allowed")

    return claims

from fastapi import Depends

def require_operator_auth(request: Request) -> dict:
    return verify_operator_request(request)

OperatorClaims = Depends(require_operator_auth)
