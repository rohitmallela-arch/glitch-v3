# FREEZE — TELEGRAM IDENTITY INVARIANT PROMOTED

- Date (UTC): 2026-02-24T015827Z
- Project: theglitchapp
- Region: us-central1
- Service: glitch-webhook
- Public URL: https://glitch-webhook-dmsse4fh6q-uc.a.run.app

## What shipped
- Enforced invariant: **one Telegram chat_id maps to exactly one canonical user_id**
- Mechanism: reverse index Firestore collection `telegram_chat_to_user/{chat_id}`
- Behavior: if chat_id already linked to a different user_id, **fail-closed** and do not relink.

## Cloud Run state (at freeze)
- 100% traffic revision: glitch-webhook-00288-quh
- Prod tag: tg-id-inv-clean
- Rollback tag preserved: rollback-prod -> glitch-webhook-00157-wsz (0%)

## Repo custody
- Repo: /Users/rohitmallela/repos/glitch-v3
- Branch: phaseV1-variant-model
- Key commits:
  - feat: enforce telegram_chat_id uniqueness via reverse index (f7a30c2)
  - chore: remove temporary telegram link invariant test harness (post-validation)

## Verification evidence
- Canary validation:
  - /health revision matched canary revision
  - Operator auth verified via /admin/whoami
  - Conflict attempt returned: `telegram_chat_already_linked` with existing_user_id = u_20260217T074914Z_4462
- Harness endpoint removed before promotion (404 confirmed)

