# Environment Variables (Glitch v2)

## Core
- `ENVIRONMENT` (default: production)
- `FIRESTORE_PROJECT_ID` (optional if ADC provides project)
- `APP_BASE_URL` (required for Stripe success/cancel URLs)

## Operator Auth (Cloud Scheduler / Admin)
- `OPERATOR_AUTH_AUDIENCE` (required) — Cloud Run service URL audience used in OIDC tokens
- `OPERATOR_INVOKER_SUBS` (comma-separated Google subject IDs) — optional allowlist
- `OPERATOR_INVOKER_EMAILS` (comma-separated emails) — optional allowlist

## Ingestion
- `INGEST_MODE` = `baseline` or `delta`
- `OPENFDA_SHORTAGE_URL` default `https://api.fda.gov/drug/shortages.json`
- `OPENFDA_LIMIT` default `100`
- `MAX_SWEEP_ITEMS` default `5000` (fail-closed cap)

## DailyMed
- `GCS_DAILYMED_BUCKET` (required for bulk ingest)
- `DAILMED_BULK_URL` (optional; preferred to use direct bulk ZIP URL via endpoint param)

## Messaging
- `TELEGRAM_BOT_TOKEN` (required for Telegram)
- SMS placeholders: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`

## Billing
- `PAYMENTS_ENABLED` (true/false)
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID`

## Limits
- `FAIL_CLOSED_LIMITS` (true/false)
- `MAX_WATCHLIST_ITEMS`
- `MAX_ALERTS_PER_DAY`
- `MAX_ALERTS_PER_NDC_PER_DAY`
- `WEEKLY_RECAP_MAX_ITEMS`
