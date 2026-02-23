# FREEZE — ALERT NAME + HYPHENATED NDC PROMOTED (2026-02-23)

## What changed
Glitch alerts now render a user-friendly drug name and a hyphenated NDC, instead of "Unknown drug" + raw NDC digits when naming is missing.

## Code changes
- Commit bb40147a87801eee385980c55cfa59b68ef634b3
  - Include `presentation` in alert payload (ingest/shortage_sweeper.py)
  - Formatter prefers `presentation` as display name and extracts hyphenated NDC (alerts/formatter.py)

- Commit 2125794191ece70b1a700d62a9f9c6d84cd7e6e7
  - Add operator-auth-only endpoint `POST /admin/test_shortage_alert`
  - Purpose: deterministic verification of formatter output end-to-end

## Infra / runtime
- Project: theglitchapp
- Region: us-central1
- Cloud Run service: glitch-webhook
- Promoted revision (100% traffic): glitch-webhook-00282-zac
- Canary tag (0% before promotion): alert-name-v1-canary
- Rollback pointer preserved: rollback-prod -> glitch-webhook-00157-wsz

## Verification (proven)
- Canary verified: POST /admin/test_shortage_alert sent Telegram message with:
  - "Reyvow, Tablet, 50 mg"
  - "NDC: 0002-4312-08"
- Prod verified with OPERATOR_AUTH_AUDIENCE token:
  - OPERATOR_AUTH_AUDIENCE=https://glitch-webhook-129120132071.us-central1.run.app

## Notes / follow-ups
- Non-blocking: GCP project still lacks environment tag; causes gcloud warning.
- Optional hygiene: multiple users share same telegram_chat_id; investigate dedupe later.
- Optional privacy: delivery logs store raw Telegram response; consider redaction later.
