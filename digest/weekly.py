from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from repos.watchlist_repo import WatchlistRepository
from repos.shortage_repo import ShortageRepository
from messaging.dispatcher import MessageDispatcher

log = logging.getLogger("glitch.digest.weekly")


def build_digest_lines(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "No monitored NDCs yet."
    lines = []
    for it in items:
        name = it.get("brand_name") or it.get("generic_name") or "Unknown drug"
        ndc = it.get("ndc_digits")
        status = it.get("status") or "unknown"
        lines.append(f"• <b>{name}</b> (<code>{ndc}</code>): <b>{status}</b>")
    return "\n".join(lines)


def run_weekly_digest_for_user(user_id: str, telegram_chat_id: str) -> Dict[str, Any]:
    wl = WatchlistRepository()
    sr = ShortageRepository()
    disp = MessageDispatcher()

    watched = wl.list_ndcs(user_id)
    enriched = []
    for w in watched:
        ndc = w["ndc_digits"]
        s = sr.get(ndc) or {}
        enriched.append({
            "ndc_digits": ndc,
            "brand_name": s.get("brand_name",""),
            "generic_name": s.get("generic_name",""),
            "status": s.get("status",""),
        })

    msg = (
        f"<b>Glitch Weekly Digest</b>\n"
        f"Week of {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
        f"{build_digest_lines(enriched)}"
    )

    resp = disp.send_telegram(chat_id=telegram_chat_id, text=msg)
    return {"ok": True, "sent": bool(resp.get("ok")), "resp": resp, "count": len(enriched)}
