from __future__ import annotations

from typing import Any, Dict, Optional
from repos.ndc_index_repo import NDCIndexRepository
from repos.ndc_alias_override_repo import NDCAliasOverrideRepository
from ndc.normalizer import normalize_ndc_to_11


class NDCResolver:
    """Resolve NDC → canonical drug names.

    Primary: DailyMed index (Firestore ndc_index)
    Fallback: openFDA shortage record fields (brand/generic/manufacturer) when available
    """

    def __init__(self, repo: Optional[NDCIndexRepository] = None, overrides: Optional[NDCAliasOverrideRepository] = None):
        self.repo = repo or NDCIndexRepository()
        self.overrides = overrides or NDCAliasOverrideRepository()

    def resolve_from_index(self, ndc: str) -> Optional[Dict[str, Any]]:
        ndc11 = normalize_ndc_to_11(ndc)
        if not ndc11:
            return None
        return self.repo.get(ndc11)

    def resolve_with_fallback(self, ndc: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        ndc11 = normalize_ndc_to_11(ndc)
        if not ndc11:
            return {
                "ndc_digits": "",
                "brand_name": "",
                "generic_name": "",
                "manufacturer": "",
                "source": "invalid_ndc",
            }

        ov = self.overrides.get(ndc11)
        if ov:
            return {
                "ndc_digits": ndc11,
                "brand_name": ov.get("brand_name", ""),
                "generic_name": ov.get("generic_name", ""),
                "manufacturer": ov.get("manufacturer", ""),
                "source": "override",
            }

        rec = self.repo.get(ndc11)
        if rec:
            return rec
        # fallback fields from openFDA shortage record, normalized to our schema
        return {
            "ndc_digits": ndc11,
            "brand_name": fallback.get("brand_name") or fallback.get("proprietary_name") or "",
            "generic_name": fallback.get("generic_name") or fallback.get("nonproprietary_name") or "",
            "manufacturer": fallback.get("manufacturer") or fallback.get("labeler_name") or "",
            "source": "openfda_fallback",
        }
