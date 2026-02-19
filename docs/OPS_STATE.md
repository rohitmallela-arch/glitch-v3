# OPS_STATE — Glitch App

- Captured (UTC): 2026-02-19T08:18:56Z
- Project: theglitchapp
- Region: us-central1
- Service: glitch-webhook
- Expected serving revision: glitch-webhook-00157-wsz

## Repo Custody
```
PWD=/Users/rohitmallela/repos/glitch-v3
TOPLEVEL=/Users/rohitmallela/repos/glitch-v3
REMOTE=git@github.com:rohitmallela-arch/glitch-v3.git
BRANCH=phaseV1-variant-model
HEAD=b6e3863
```

## Cloud Run — Service Describe (status.url / traffic / latestReadyRevisionName)
```json
{
  "status": {
    "latestReadyRevisionName": "glitch-webhook-00157-wsz",
    "traffic": [
      {
        "revisionName": "glitch-webhook-00128-66n",
        "tag": "openfda-canary",
        "url": "https://openfda-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00129-xxs",
        "tag": "openfda",
        "url": "https://openfda---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00137-rdc",
        "tag": "hashfix-canary",
        "url": "https://hashfix-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00138-mbs",
        "tag": "hashdebug-canary",
        "url": "https://hashdebug-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "percent": 100,
        "revisionName": "glitch-webhook-00157-wsz"
      },
      {
        "revisionName": "glitch-webhook-00173-nil",
        "tag": "variant-model-canary",
        "url": "https://variant-model-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00176-yup",
        "tag": "phase-v2-canary",
        "url": "https://phase-v2-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00178-hab",
        "tag": "phase-v2-health",
        "url": "https://phase-v2-health---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00180-loq",
        "tag": "signup-fix-canary",
        "url": "https://signup-fix-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00181-zob",
        "tag": "signup-fix2-canary",
        "url": "https://signup-fix2-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00183-tih",
        "tag": "stripe-appbase-canary",
        "url": "https://stripe-appbase-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00184-tik",
        "tag": "stripe-checkout-canary",
        "url": "https://stripe-checkout-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00186-ric",
        "tag": "operator-auth-fix-canary",
        "url": "https://operator-auth-fix-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      },
      {
        "revisionName": "glitch-webhook-00128-66n",
        "tag": "operator-auth-canary",
        "url": "https://operator-auth-canary---glitch-webhook-dmsse4fh6q-uc.a.run.app"
      }
    ],
    "url": "https://glitch-webhook-dmsse4fh6q-uc.a.run.app"
  }
}
```

## Cloud Run — Runtime Service Account
```
129120132071-compute@developer.gserviceaccount.com
```

## Cloud Run — Serving Revision Image Digest
```
us-central1-docker.pkg.dev/theglitchapp/cloud-run-source-deploy/glitch-webhook@sha256:22cf9a680c8e8ef6c49734c4972acd352e16843be0855bb36bc93ada8d0925bc
```

## Cloud Run — Serving Revision Env (authoritative)
```json
{
  "spec": {
    "containers": [
      {
        "env": [
          {
            "name": "STRIPE_API_KEY",
            "valueFrom": {
              "secretKeyRef": {
                "key": "latest",
                "name": "stripe_api_key_test"
              }
            }
          },
          {
            "name": "STRIPE_WEBHOOK_SECRET",
            "valueFrom": {
              "secretKeyRef": {
                "key": "5",
                "name": "stripe_webhook_secret_test"
              }
            }
          },
          {
            "name": "TWILIO_ACCOUNT_SID",
            "valueFrom": {
              "secretKeyRef": {
                "key": "latest",
                "name": "TWILIO_ACCOUNT_SID"
              }
            }
          },
          {
            "name": "TWILIO_AUTH_TOKEN",
            "valueFrom": {
              "secretKeyRef": {
                "key": "latest",
                "name": "TWILIO_AUTH_TOKEN"
              }
            }
          },
          {
            "name": "TWILIO_FROM_NUMBER",
            "valueFrom": {
              "secretKeyRef": {
                "key": "latest",
                "name": "TWILIO_NUMBER"
              }
            }
          },
          {
            "name": "TWILIO_NUMBER",
            "valueFrom": {
              "secretKeyRef": {
                "key": "latest",
                "name": "TWILIO_NUMBER"
              }
            }
          },
          {
            "name": "TELEGRAM_BOT_TOKEN",
            "valueFrom": {
              "secretKeyRef": {
                "key": "latest",
                "name": "TELEGRAM_BOT_TOKEN"
              }
            }
          },
          {
            "name": "APP_BASE_URL",
            "value": "https://glitch-webhook-dmsse4fh6q-uc.a.run.app"
          },
          {
            "name": "PAYMENTS_ENABLED",
            "value": "true"
          },
          {
            "name": "STRIPE_PRICE_ID",
            "value": "price_1Sv5eSAbml4ATQdpoqzuV2RH"
          },
          {
            "name": "CHECKOUT_SUCCESS_URL",
            "value": "https://example.com/success"
          },
          {
            "name": "CHECKOUT_CANCEL_URL",
            "value": "https://example.com/cancel"
          },
          {
            "name": "OPERATOR_AUTH_AUDIENCE",
            "value": "https://glitch-webhook-129120132071.us-central1.run.app"
          },
          {
            "name": "OPERATOR_INVOKER_EMAILS",
            "value": "glitch-scheduler-sa@theglitchapp.iam.gserviceaccount.com"
          },
          {
            "name": "CONFIG_BUMP",
            "value": "bump_20260217T102040Z"
          }
        ]
      }
    ]
  }
}
```

## Notes / Drift Risks
- Secrets using latest: stripe_api_key_test, TELEGRAM_BOT_TOKEN, TWILIO_*
- Checkout URLs currently placeholders (example.com)

