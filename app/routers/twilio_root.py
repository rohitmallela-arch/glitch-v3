from __future__ import annotations

from fastapi import APIRouter
from app.routers.messaging import twilio_inbound  # re-export handler

router = APIRouter()
router.add_api_route("/twilio/inbound", twilio_inbound, methods=["POST"])
