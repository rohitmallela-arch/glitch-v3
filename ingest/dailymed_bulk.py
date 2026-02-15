from __future__ import annotations

import io
import logging
import re
import zipfile
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple
from xml.etree import ElementTree as ET

import requests

from config.settings import settings
from storage.gcs_client import upload_bytes
from repos.ndc_index_repo import NDCIndexRepository
from ndc.normalizer import normalize_ndc_to_11

log = logging.getLogger("glitch.ingest.dailymed")

# DailyMed bulk files vary. This ingestor supports:
# - Direct URL to a zip containing SPL XML files
# - Zip that contains subfolders
#
# We parse SPL XML looking for NDC-like content and common SPL structures.
# This is intentionally robust and defensive.

NDC_RE = re.compile(r"(\d{4,5})[- ]?(\d{3,4})[- ]?(\d{1,2})")


def download_bulk_zip(url: str) -> bytes:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.content


def iter_xml_files_from_zip(zip_bytes: bytes) -> Iterable[Tuple[str, bytes]]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            if name.lower().endswith(".xml"):
                yield name, z.read(name)


def extract_ndcs_from_spl_xml(xml_bytes: bytes) -> Iterable[str]:
    # Strategy:
    # 1) Try structured tags if present (varies)
    # 2) Fallback: regex scan of text content for NDC patterns
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return []

    found = set()

    # Structured attempt: scan all text nodes for patterns
    for elem in root.iter():
        if elem.text:
            for m in NDC_RE.finditer(elem.text):
                ndc = "".join(m.groups())
                ndc11 = normalize_ndc_to_11(ndc)
                if ndc11:
                    found.add(ndc11)

    return list(found)


def build_ndc_index_from_bulk_zip(url: str, gcs_bucket: str) -> Dict[str, int]:
    if not gcs_bucket:
        raise RuntimeError("GCS_DAILYMED_BUCKET not configured")

    zip_bytes = download_bulk_zip(url)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    gcs_path = upload_bytes(gcs_bucket, f"dailymed/bulk_{ts}.zip", zip_bytes, content_type="application/zip")
    log.info("dailymed bulk downloaded", extra={"extra": {"gcs_path": gcs_path, "bytes": len(zip_bytes)}})

    repo = NDCIndexRepository()
    xml_count = 0
    ndc_count = 0

    for name, xml in iter_xml_files_from_zip(zip_bytes):
        xml_count += 1
        ndcs = extract_ndcs_from_spl_xml(xml)
        if not ndcs:
            continue
        for ndc11 in ndcs:
            # For MVP, we only guarantee NDC presence; name fields can be enriched later by deeper SPL parsing.
            # We still keep schema stable and allow future enrich.
            repo.upsert(ndc11, {
                "ndc_digits": ndc11,
                "brand_name": "",
                "generic_name": "",
                "manufacturer": "",
                "source": "dailymed_bulk",
                "spl_xml_source": name,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            ndc_count += 1

    return {"xml_files": xml_count, "ndc_upserts": ndc_count}
