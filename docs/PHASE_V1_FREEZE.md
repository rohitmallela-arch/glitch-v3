# 🔒 GLITCH APP — PHASE V1 FREEZE
Date: 2026-02-16
Status: PRODUCTION STABLE

---

## 1️⃣ Deployment State

Project: theglitchapp  
Region: us-central1  
Service: glitch-webhook  

Serving Revision:
glitch-webhook-00173-nil

Traffic:
100% → glitch-webhook-00173-nil

---

## 2️⃣ Variant Model Architecture

### Firestore Structure

Collection:
shortages/{ndc11}

Parent document contains:
- headline fields
- headline_variant_key
- headline_snapshot_hash
- variants_count

Subcollection:
shortages/{ndc11}/variants/{variant_key}

Each variant stores:
- status
- presentation
- reason
- resolution
- snapshot_hash

---

## 3️⃣ Deterministic Headline Contract

Headline selection rule:
- Lexicographically smallest variant_key

Delta comparison rule:
- Compare headline_snapshot_hash only
- Do NOT compare variant subdocuments directly

Result:
- No variant flip-flop
- No duplicate alerts
- Stable delta behavior

---

## 4️⃣ Delta Engine Invariants

Validated Production Output:
processed: 1740
changed: 0
baseline_completed: true

Three consecutive deterministic executions confirmed stability.

---

## 5️⃣ Operator Auth Contract

Environment Variables:

OPERATOR_AUTH_AUDIENCE =
https://glitch-webhook-129120132071.us-central1.run.app

OPERATOR_INVOKER_EMAILS =
glitch-scheduler-sa@theglitchapp.iam.gserviceaccount.com

Token mint rule:
- Always impersonate glitch-scheduler-sa
- Audience MUST match OPERATOR_AUTH_AUDIENCE
- Never derive audience from service URL automatically

---

## 6️⃣ Canonical URLs

Service URL (runtime):
https://glitch-webhook-dmsse4fh6q-uc.a.run.app

Canonical Audience URL (auth validation):
https://glitch-webhook-129120132071.us-central1.run.app

These are intentionally different.

---

## 7️⃣ Rollback Procedure

To rollback to stable revision:

gcloud run services update-traffic glitch-webhook \
  --region us-central1 \
  --to-revisions=glitch-webhook-00136-6rw=100

---

## 8️⃣ DO NOT BREAK

- Do not overwrite parent doc with variant snapshots.
- Do not compare variant docs directly in delta logic.
- Do not change headline selection rule.
- Do not change operator audience without updating validation logic.
- Do not use --to-latest for traffic shifts.

---

Phase V1 declared stable and frozen.
