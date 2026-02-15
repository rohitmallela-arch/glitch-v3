from __future__ import annotations

import re

# NDC may come in 10-digit or 11-digit forms. openFDA package_ndc includes hyphens.
# True 10→11 conversion depends on segment pattern; if unknown, we left-pad to 11.
# Deterministic rule for Glitch: digits only, left-pad to 11 (matches prior behavior).
def normalize_ndc_to_11(ndc: str) -> str:
    digits = re.sub(r"\D", "", ndc or "")
    if not digits:
        return ""
    if len(digits) > 11:
        # Sometimes NDC appears embedded; keep last 11 as safest heuristic
        digits = digits[-11:]
    return digits.zfill(11)
