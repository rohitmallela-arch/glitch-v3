from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ops.structured_logger import setup_logging

from app.routers.health import router as health_router
from app.routers.users import router as users_router
from app.routers.billing import router as billing_router
from app.routers.watchlist import router as watchlist_router
from app.routers.messaging import router as messaging_router
from app.routers.admin import router as admin_router
from app.routers.ui import router as ui_router
from app.routers.twilio_root import router as twilio_root_router
from app.routers.telegram_root import router as telegram_root_router
from app.routers.auth import router as auth_router

setup_logging()

app = FastAPI(title="Glitch API", version="3.0.0")

# CORS needed for browser-based /ui/* transparency endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(billing_router, prefix="/api", tags=["billing"])
app.include_router(watchlist_router, prefix="/api", tags=["watchlist"])
app.include_router(messaging_router, prefix="/api", tags=["messaging"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(ui_router, tags=["ui"])
app.include_router(auth_router, tags=["auth"])
app.include_router(twilio_root_router, tags=["twilio"])
app.include_router(telegram_root_router, tags=["telegram"])
