# Glitch v3 (End-to-End)

Glitch is a deterministic drug shortage alerting platform built for independent pharmacies.

## Product flow (target)
1. User signs up
2. User pays (Stripe checkout)
3. User connects Telegram (and later SMS)
4. User creates NDC watchlist
5. Welcome message delivered
6. System runs baseline ingest (no alerts)
7. System runs delta sweeps (alert only on changes; silent otherwise)
8. Weekly digest summarizing watchlist shortages

## Architecture
- FastAPI for API service + ingest/admin endpoints
- Firestore for application data
- GCS for DailyMed bulk storage
- Stripe for billing (test mode supported)
- Telegram for messaging (SMS abstraction included; Twilio later)

## Services
- **API service**: `app.api_service:app` (default Docker CMD)
- **Ingest service**: can run as Cloud Run Job or service using `app.ingest_service:app` or module runners in `ops/runbooks/`.

## Quickstart (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export FIRESTORE_PROJECT_ID="theglitchapp"
export GCS_DAILYMED_BUCKET="YOUR_BUCKET"
export STRIPE_API_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
export STRIPE_PRICE_ID="price_..."
export TELEGRAM_BOT_TOKEN="..."
export APP_BASE_URL="https://your-service-url"

uvicorn app.api_service:app --reload
```

## Docs
- `docs/FIRESTORE_SCHEMA.md`
- `docs/ENV_VARS.md`
- `docs/RUNBOOK.md`
