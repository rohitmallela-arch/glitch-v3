from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from ops.structured_logger import setup_logging
from security.operator_auth import verify_operator_request
from config.settings import settings
from ingest.shortage_sweeper import sweep_all_shortages, upsert_and_detect_changes
from ingest.dailymed_bulk import build_ndc_index_from_bulk_zip

setup_logging()

log = logging.getLogger("glitch.ingest.service")

app = FastAPI(title="Glitch Ingest", version="3.0.0")


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
            extra={"extra": {"stage": "fetch", "mode": settings.INGEST_MODE, "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    try:
        result = upsert_and_detect_changes(recs, mode=settings.INGEST_MODE)
    except Exception as e:
        log.error(
            "delta_error",
            extra={"extra": {"stage": "upsert", "mode": settings.INGEST_MODE, "error_type": type(e).__name__, "message": str(e)}},
            exc_info=True,
        )
        raise
    return {"ok": True, "mode": settings.INGEST_MODE, "meta": meta, "result": result}


@app.post("/dailymed_bulk_ingest")
def dailymed_bulk_ingest(request: Request, url: str):
    verify_operator_request(request)
    stats = build_ndc_index_from_bulk_zip(url=url, gcs_bucket=settings.GCS_DAILYMED_BUCKET)
    return {"ok": True, "stats": stats}
