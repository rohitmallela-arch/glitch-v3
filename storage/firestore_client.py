from __future__ import annotations

from google.cloud import firestore
from config.settings import settings


def get_firestore_client() -> firestore.Client:
    # If FIRESTORE_PROJECT_ID is empty, the library will use ADC default project.
    if settings.FIRESTORE_PROJECT_ID:
        return firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
    return firestore.Client()
