# GLITCH APP — INFRA FREEZE
Date: 2026-02-21

## Cloud Run
Service: glitch-webhook
Region: us-central1
100% Traffic Revision: glitch-webhook-opaud-1771674948
Base URL: https://glitch-webhook-dmsse4fh6q-uc.a.run.app
OIDC Audience: https://glitch-webhook-129120132071.us-central1.run.app

## Billing
- Stripe checkout → active subscription confirmed
- customer.subscription.deleted → inactive confirmed
- /ui/me reflects correct subscription state

## Scheduler Jobs
- glitch-shortage-poller → POST /admin/run_delta_now (OIDC working)
- glitch-weekly-recap → POST /admin/weekly_recap_run (OIDC configured)
- morning-price-check → GET /health
- hourly-pharma-check → GET /health

## Proven End-to-End
- Scheduler → Cloud Run OIDC validated
- Operator auth audience validated
- Revision routing confirmed
- Traffic pinned to correct revision
- No 404 noise
- No 500 auth errors
