from __future__ import annotations

import logging
import os
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from config.settings import settings
from ingest.dailymed_bulk import build_ndc_index_from_bulk_zip
from ingest.shortage_sweeper import sweep_all_shortages, upsert_and_detect_changes
from ops.structured_logger import setup_logging
from security.operator_auth import verify_operator_request

setup_logging()

log = logging.getLogger("glitch.ingest.service")

app = FastAPI(title="Glitch Ingest", version="3.0.0")


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or ""


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
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


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "glitch-ingest"}


@app.post("/shortage_baseline_run")
def shortage_baseline_run(request: Request):
    verify_operator_request(request)
    try:
        recs, meta = sweep_all_shortages()
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "fetch", "mode": "baseline", "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    try:
        result = upsert_and_detect_changes(recs, mode="baseline")
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "upsert", "mode": "baseline", "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    return {"ok": True, "mode": "baseline", "meta": meta, "result": result}


@app.post("/shortage_poll_run")
def shortage_poll_run(request: Request):
    verify_operator_request(request)
    try:
        recs, meta = sweep_all_shortages()
    except Exception as e:
        log.error(
            "delta_error",
            extra={
                "extra": {
                    "stage": "fetch",
                    "mode": settings.INGEST_MODE,
                    "error_type": type(e).__name__,
                    "message": str(e),
                }
            },
            exc_info=True,
        )
        raise
    try:
        result = upsert_and_detect_changes(recs, mode=settings.INGEST_MODE)
    except Exception as e:
        log.error(
            "delta_error",
            extra={
                "extra": {
                    "stage": "upsert",
                    "mode": settings.INGEST_MODE,
                    "error_type": type(e).__name__,
                    "message": str(e),
                }
            },
            exc_info=True,
        )
        raise
    return {"ok": True, "mode": settings.INGEST_MODE, "meta": meta, "result": result}


@app.post("/dailymed_bulk_ingest")
def dailymed_bulk_ingest(request: Request, url: str):
    verify_operator_request(request)
    stats = build_ndc_index_from_bulk_zip(url=url, gcs_bucket=settings.GCS_DAILYMED_BUCKET)
    return {"ok": True, "stats": stats}
