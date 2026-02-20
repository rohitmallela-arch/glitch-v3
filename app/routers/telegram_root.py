from __future__ import annotations

from fastapi import APIRouter

from app.routers.messaging import telegram_inbound

router = APIRouter()
router.add_api_route("/telegram/inbound", telegram_inbound, methods=["POST"])
