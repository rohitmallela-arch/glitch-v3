from __future__ import annotations

from typing import Any, Dict

import re


def _ndc_display(payload: Dict[str, Any]) -> str:
    """
    Prefer hyphenated NDC extracted from 'presentation' (e.g. '... (NDC 0002-4312-08)').
    Fallback to raw ndc_digits.
    """
    pres = (payload.get("presentation") or "").strip()
    if pres:
        m = re.search(r"\bNDC\s+([0-9]{4,5}-[0-9]{3,4}-[0-9]{1,2})\b", pres, flags=re.I)
        if m:
            return m.group(1)
    ndc = (payload.get("ndc_digits") or "").strip()
    return ndc


def _display_name(payload: Dict[str, Any]) -> str:
    pres = (payload.get("presentation") or "").strip()
    brand = (payload.get("brand_name") or "").strip()
    generic = (payload.get("generic_name") or "").strip()

    # Presentation is most user-friendly (often includes brand + form + strength).
    if pres:
        # Strip trailing '(NDC ...)' so name line isn't noisy; NDC is shown separately.
        name = re.sub(r"\s*\(NDC\s+[0-9-]+\)\s*$", "", pres, flags=re.I).strip()
        return name or pres

    return brand or generic or "Unknown drug"


def format_shortage_change_alert(payload: Dict[str, Any]) -> str:
    brand = payload.get("brand_name") or ""
    generic = payload.get("generic_name") or ""
    mfg = payload.get("manufacturer") or ""
    ndc_digits = payload.get("ndc_digits") or ""
    ndc_disp = _ndc_display(payload) or ndc_digits or ""
    old_s = payload.get("old_status") or "unknown"
    new_s = payload.get("new_status") or "unknown"
    last = payload.get("last_updated") or ""

    name = _display_name(payload)
    extra = []
    if generic and (not name.lower().startswith(generic.lower())) and (generic.lower() != (brand or "").lower()):
        extra.append(f"Generic: {generic}")
    if mfg:
        extra.append(f"Manufacturer: {mfg}")
    extra_txt = "\n".join(extra)
    last_line = f"Last Updated: {last}\n" if last else ""

    return (
        f"<b>Glitch Alert</b>\n"
        f"<b>{name}</b>\n"
        f"NDC: <code>{ndc_disp}</code>\n"
        f"Status: <b>{old_s}</b> → <b>{new_s}</b>\n"
        f"{last_line}"
        f"{extra_txt}"
    ).strip()
