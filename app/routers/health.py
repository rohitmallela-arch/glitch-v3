from __future__ import annotations

import os
import time
from typing import Any, Dict

from fastapi import APIRouter

from config.settings import settings

router = APIRouter()


def _firestore_probe(timeout_s: float = 0.20) -> Dict[str, Any]:
    """
    Read-only, bounded-time Firestore connectivity probe.
    - No PII
    - No writes
    - Uses a fixed doc path.
    """
    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        return {"ok": False, "error_type": type(e).__name__, "message": str(e)}

    try:
        t0 = time.time()
        db = firestore.Client(project=settings.FIRESTORE_PROJECT_ID or None)
        # Read-only: a single doc get with timeout.
        db.collection("system").document("healthz").get(timeout=timeout_s)
        dt_ms = int((time.time() - t0) * 1000)
        return {"ok": True, "latency_ms": dt_ms}
    except Exception as e:
        return {"ok": False, "error_type": type(e).__name__, "message": str(e)}


@router.get("/health")
def health():
    rev = os.getenv("K_REVISION") or ""
    svc = os.getenv("K_SERVICE") or "glitch-webhook"

    fs = _firestore_probe()

    payload: Dict[str, Any] = {
        "ok": True,
        "service": "glitch-api",
        "cloudrun_service": svc,
        "revision": rev,
        "environment": settings.ENVIRONMENT,
        "payments_enabled": bool(settings.PAYMENTS_ENABLED),
        "firestore_ok": bool(fs.get("ok", False)),
        "firestore": fs,
        "time_unix": time.time(),
    }

    # If fail-closed is enabled, surface degraded signals explicitly.
    if settings.FAIL_CLOSED_LIMITS and not payload["firestore_ok"]:
        payload["ok"] = False

    return payload
