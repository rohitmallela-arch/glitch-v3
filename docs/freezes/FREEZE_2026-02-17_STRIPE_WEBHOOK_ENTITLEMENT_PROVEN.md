# 🔒 GLITCH APP — FREEZE DOCUMENT
## POST-STRIPE WEBHOOK FIX + ENTITLEMENT PROVEN
Date: 2026-02-17

Project: theglitchapp  
Region: us-central1  
Service: glitch-webhook  

---

## 1) Cloud Run Identity + Routing (VERIFIED)

Public Service URL:
https://glitch-webhook-dmsse4fh6q-uc.a.run.app

Operator Auth Audience:
https://glitch-webhook-129120132071.us-central1.run.app

Serving Revision (100% traffic):
glitch-webhook-00151-9qb

---

## 2) Runtime Service Account (VERIFIED)

Runtime SA:
129120132071-compute@developer.gserviceaccount.com

IAM:
roles/secretmanager.secretAccessor → confirmed

---

## 3) Stripe Webhook Signing Secret (PINNED)

Secret:
stripe_webhook_secret_test

Pinned Version in Serving Revision:
STRIPE_WEBHOOK_SECRET = stripe_webhook_secret_test:5

Never use "latest" for Stripe webhook secrets in production.

---

## 4) Stripe Lifecycle (PROVEN)

Flow Proven:
Signup → Telegram bind → Checkout → Webhook → Entitlement unlock

Pre-webhook:
402 subscription_required

Post-webhook:
200 OK

Webhook signature verification:
HTTP 200 confirmed after secret alignment.

---

## 5) Root Cause Summary

Time was lost due to:

1. Webhook endpoint path mismatch
2. Stripe CLI misuse (URL instead of we_ endpoint ID)
3. Secret mismatch across environments
4. Cloud Run revision not serving traffic

Deterministic Fix Pattern:
1. Recreate webhook endpoint
2. Store new signing secret in Secret Manager
3. Pin explicit secret version
4. Move traffic explicitly
5. Resend event using we_ endpoint ID

---

## 6) Anti-Spiral Rules (Binding)

- Never assume latest revision is serving traffic
- Always verify percent=100 revision
- Always verify runtime SA from serving revision
- Always verify secret version key (not latest)
- Always move traffic explicitly
- Always use Stripe endpoint ID (we_...) when resending events

---

## 7) System State at Freeze

Serving Revision:
glitch-webhook-00151-9qb

Runtime SA:
129120132071-compute@developer.gserviceaccount.com

Secret Binding:
stripe_webhook_secret_test:5

Revenue Lifecycle:
Fully Proven

Delta Engine:
Operational

Watchlist Gating:
Operational

Remaining Work:
POST /admin/test_alert (deterministic forced alert endpoint)

---

Freeze Status: Operationally Stable
