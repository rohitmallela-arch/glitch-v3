# GLITCH — FREEZE: Phase V2 Observability Promoted

Timestamp (UTC): 2026-02-20T01:11:57Z

## Cloud Run
Project: theglitchapp
Region: us-central1
Service: glitch-webhook

Prod traffic: 100% -> glitch-webhook-00204-buv  
Rollback tag: rollback-prod -> glitch-webhook-00157-wsz

## Canary image digest (00204-buv)
us-central1-docker.pkg.dev/theglitchapp/cloud-run-source-deploy/glitch-webhook@sha256:431e1fa8c8f22ab593a42c8dd8825cc3ec7d8bc94681c05f55cb104a387d4989

## Monitoring
Uptime check path: /health (no trailing slash)
Uptime alert policy: Glitch Webhook Uptime Failed (/health)

Log-based metrics alert policies enabled:
- Glitch: Telegram exceptions > 0 (5m)
- Glitch: Max sweep cap exceeded > 0 (5m)
- Glitch: Delta anomaly > 0 (5m)

## Operator auth (verified earlier)
Audience: https://glitch-webhook-129120132071.us-central1.run.app
Endpoints verified: /admin/whoami (200), /admin/run_delta_now (200)
