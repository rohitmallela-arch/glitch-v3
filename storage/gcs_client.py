from __future__ import annotations

from google.cloud import storage
from config.settings import settings


def get_gcs_client() -> storage.Client:
    return storage.Client()


def upload_bytes(bucket_name: str, blob_name: str, content: bytes, content_type: str = "application/octet-stream") -> str:
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(content, content_type=content_type)
    return f"gs://{bucket_name}/{blob_name}"
