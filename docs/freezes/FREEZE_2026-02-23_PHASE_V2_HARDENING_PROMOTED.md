# FREEZE — PHASE V2 HARDENING PROMOTED (2026-02-23)

## Scope
Glitch App Phase V2 reliability hardening promoted to production:
- Telegram token rotated (prior token exposure contained)
- request_id propagation into send logs
- canary-first deployment discipline adhered
- prod promotion verified with real Telegram traffic

## Repo Custody
- repo: /Users/rohitmallela/repos/glitch-v3
- remote: git@github.com:rohitmallela-arch/glitch-v3.git
- branch: phaseV1-variant-model
- head: c2b2753789ba8b5fe8256127994241c2fd5a5a6a

## Cloud Run
- project_id: theglitchapp
- region: us-central1
- service: glitch-webhook
- service_url: https://glitch-webhook-dmsse4fh6q-uc.a.run.app

### Traffic (as of 2026-02-23T045642Z)
- promoted_revision (100%): glitch-webhook-00201-h9t
- rollback_prod (tag): rollback-prod -> glitch-webhook-00157-wsz
- canary_tag: phase-v2-obs-canary -> glitch-webhook-00201-h9t
- other_tags: auth-v1-canary, contract-v2-canary (0%)

## Telegram
- webhook_url (steady-state): https://glitch-webhook-dmsse4fh6q-uc.a.run.app/telegram/inbound
- bot_token secret: TELEGRAM_BOT_TOKEN
- bot_token pinned version (runtime verified): 3
- verification: prod /telegram/inbound 200 + telegram_send_* logs include non-empty request_id

## Observability
- structured logs: JsonFormatter + secret leakage suppression (httpx/httpcore WARN)
- request_id: ContextVar set/cleared in middleware; injected into payload when missing/empty
- verified in prod: telegram_send_attempt/result show request_id (non-empty)

## Known Governance Nits
- GCP project lacks 'environment' tag (non-blocking): theglitchapp

## Rollback
- Immediate rollback target: glitch-webhook-00157-wsz
- Command:
  gcloud run services update-traffic glitch-webhook --project theglitchapp --region us-central1 --to-revisions glitch-webhook-00157-wsz=100
