from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Core
    ENVIRONMENT: str = Field(default="production")
    FIRESTORE_PROJECT_ID: str = Field(default="")
    APP_BASE_URL: str = Field(default="")  # canonical Cloud Run URL for deep links

    # Operator/admin auth (Google OIDC ID token)
    OPERATOR_AUTH_AUDIENCE: str = Field(default="")
    OPERATOR_INVOKER_SUBS: str = Field(default="")  # comma-separated
    OPERATOR_INVOKER_EMAILS: str = Field(default="")  # comma-separated

    # Ingestion modes
    INGEST_MODE: str = Field(default="delta")  # baseline | delta
    MAX_SWEEP_ITEMS: int = Field(default=5000)
    OPENFDA_SHORTAGE_URL: str = Field(default="https://api.fda.gov/drug/shortages.json")
    OPENFDA_LIMIT: int = Field(default=100)

    # DailyMed bulk
    GCS_DAILYMED_BUCKET: str = Field(default="")
    DAILMED_BULK_URL: str = Field(
        default="https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm"
    )
    # NOTE: Above is a landing page; the ingestor supports direct URL to a zip if provided.

    # Messaging
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TWILIO_ACCOUNT_SID: str = Field(default="")
    TWILIO_AUTH_TOKEN: str = Field(default="")
    TWILIO_FROM_NUMBER: str = Field(default="")

    # Billing
    STRIPE_API_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    STRIPE_PRICE_ID: str = Field(default="")
    PAYMENTS_ENABLED: bool = Field(default=True)

    # Limits (fail-closed)
    FAIL_CLOSED_LIMITS: bool = Field(default=True)
    MAX_WATCHLIST_ITEMS: int = Field(default=25)
    MAX_ALERTS_PER_DAY: int = Field(default=20)
    MAX_ALERTS_PER_NDC_PER_DAY: int = Field(default=3)
    WEEKLY_RECAP_MAX_ITEMS: int = Field(default=20)


settings = Settings()
