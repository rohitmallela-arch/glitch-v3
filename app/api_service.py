from __future__ import annotations

import logging
import os
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from billing.entitlements import SubscriptionRequired
from ops.structured_logger import setup_logging
from utils.request_context import clear_request_id, set_request_id

from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.billing import router as billing_router
from app.routers.health import router as health_router
from app.routers.telegram_root import router as telegram_root_router
from app.routers.twilio_root import router as twilio_root_router
from app.routers.ui import router as ui_router
from app.routers.users import router as users_router
from app.routers.watchlist import router as watchlist_router

setup_logging()

app = FastAPI(title="Glitch API", version="3.0.0")
log = logging.getLogger("glitch.api")


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or ""


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    set_request_id(rid)
    try:
        response = await call_next(request)
    finally:
        clear_request_id()
    response.headers["X-Request-Id"] = rid
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    rid = _get_request_id(request)
    log.warning(
        "http_exception",
        extra={
            "extra": {
                "event": "http_exception",
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
                "method": request.method,
                "request_id": rid,
            }
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": rid, "revision": os.getenv("K_REVISION") or ""},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    rid = _get_request_id(request)
    log.warning(
        "validation_error",
        extra={
            "extra": {
                "event": "validation_error",
                "path": request.url.path,
                "method": request.method,
                "request_id": rid,
            }
        },
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "request_id": rid, "revision": os.getenv("K_REVISION") or ""},
    )


@app.exception_handler(SubscriptionRequired)
async def subscription_required_handler(request: Request, exc: SubscriptionRequired):
    # Preserve existing semantics exactly.
    return JSONResponse(
        status_code=403,
        content={"detail": "subscription_required", "status": exc.status, "upgrade_url": exc.upgrade_url},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    rid = _get_request_id(request)
    log.error(
        "internal_unhandled_exception",
        extra={
            "extra": {
                "event": "internal_unhandled_exception",
                "error_type": type(exc).__name__,
                "message": str(exc),
                "path": request.url.path,
                "method": request.method,
                "request_id": rid,
            }
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"error": "internal_unhandled_exception", "request_id": rid, "revision": os.getenv("K_REVISION") or ""},
    )


# CORS needed for browser-based /ui/* transparency endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(billing_router, prefix="/api", tags=["billing"])
app.include_router(watchlist_router, prefix="/api", tags=["watchlist"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(ui_router, tags=["ui"])
app.include_router(auth_router, tags=["auth"])
app.include_router(twilio_root_router, tags=["twilio"])
app.include_router(telegram_root_router, tags=["telegram"])
