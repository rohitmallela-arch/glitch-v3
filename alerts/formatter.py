from __future__ import annotations

from typing import Any, Dict


def format_shortage_change_alert(payload: Dict[str, Any]) -> str:
    # payload contains: ndc_digits, name fields, old_status, new_status, last_updated
    brand = payload.get("brand_name") or ""
    generic = payload.get("generic_name") or ""
    mfg = payload.get("manufacturer") or ""
    ndc = payload.get("ndc_digits") or ""
    old_s = payload.get("old_status") or "unknown"
    new_s = payload.get("new_status") or "unknown"
    last = payload.get("last_updated") or ""

    name = brand or generic or "Unknown drug"
    extra = []
    if generic and brand and generic.lower() != brand.lower():
        extra.append(f"Generic: {generic}")
    if mfg:
        extra.append(f"Manufacturer: {mfg}")
    extra_txt = "\n".join(extra)
    last_line = f"Last Updated: {last}\n" if last else ""

    return (
        f"<b>Glitch Alert</b>\n"
        f"<b>{name}</b>\n"
        f"NDC: <code>{ndc}</code>\n"
        f"Status: <b>{old_s}</b> → <b>{new_s}</b>\n"
        f"{last_line}"
        f"{extra_txt}"
    ).strip()
