# Glitch v2 Runbook (High Level)

## Build / Run locally
```bash
pip install -r requirements.txt
export FIRESTORE_PROJECT_ID=theglitchapp
export STRIPE_API_KEY=sk_test_...
export STRIPE_WEBHOOK_SECRET=whsec_...
export STRIPE_PRICE_ID=price_...
export TELEGRAM_BOT_TOKEN=...
export APP_BASE_URL=http://localhost:8000

uvicorn app.api_service:app --reload --port 8000
```

## Ingest service (admin protected)
```bash
uvicorn app.ingest_service:app --reload --port 8081
```

## Baseline (no alerts)
Call `POST /shortage_baseline_run` on ingest service with Google OIDC Authorization header.

## Delta sweeps
Set `INGEST_MODE=delta` and Scheduler hits `POST /shortage_poll_run` with OIDC token.

## DailyMed bulk ingest
Call `POST /dailymed_bulk_ingest?url=<DIRECT_ZIP_URL>` (admin protected)
Stores bulk zip in GCS and upserts NDC index.

## Deploy pattern
- Build image via Cloud Build
- Deploy `glitch-api` with concurrency > 1
- Deploy `glitch-ingest` with concurrency = 1 (or Cloud Run Job)
- Scheduler targets `glitch-ingest/shortage_poll_run`

## Twilio inbound
- POST `/twilio/inbound` (TwiML response). User texts YES to activate.

## UI transparency
- GET `/ui/status`
- POST `/ui/user/status`
- POST `/ui/user/diagnostics`

## Weekly recap
- POST `/admin/weekly_recap_run` (operator auth; scheduled weekly)
