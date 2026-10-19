# Future Backend Implementation Guide

## Purpose

The current repository provides a small **face-recognition dummy**. It compares a reference face with a probe face and returns a JSON-friendly match result. Another application can import `face_id.py` and decide what to do with that result.

The current `payment_eligible` and `payment_status` fields are dummy values only. They do **not** authorize a payment and the current code does not call Fiuu.

## Current handoff contract

```python
from face_id import FaceVerificationError, verify_face

result = verify_face(reference_image_bytes, probe_image_bytes)
```

Example response:

```json
{
  "matched": true,
  "similarity_score": 0.82,
  "threshold": 0.363,
  "payment_eligible": true,
  "payment_status": "approved_for_demo",
  "mode": "dummy"
}
```

The integrating application should treat this as a demo eligibility signal only. It must not use a facial match alone to charge a customer or complete a payment.

## Target architecture

```text
Mobile/Web app
   │
   ├── Explicit consent + account authentication
   │
   ├── Capture reference/probe image
   │
   ▼
Python backend API
   ├── Liveness / anti-spoof verification
   ├── One-to-one face verification
   ├── Encrypted biometric-template storage
   ├── Order and idempotency service
   └── Fiuu Hosted Payment Page adapter
            │
            ▼
     Customer completes Fiuu authentication
            │
            ▼
     Fiuu server-to-server notification
            │
            ▼
     Backend verifies signature and updates order status
```

## Suggested backend stack

- **API:** FastAPI or the application team's existing Python web framework.
- **Face verifier:** reuse `FaceVerifier` in `face_id.py` behind a service interface.
- **Database:** PostgreSQL for users, orders, consent records, and payment status.
- **Biometric storage:** encrypted templates only; avoid persisting raw face photos unless a documented retention requirement exists.
- **Object storage:** private, encrypted, short-lived storage only if an image must be retained for an approved purpose.
- **Background jobs:** queue webhook retries, deletion jobs, and reconciliation work.
- **Secrets:** environment-specific secret manager; never source control.

## Backend API phases

### Phase 1 — application integration

Keep the current dummy matcher and let the application call it through a narrow service function:

```python
result = verify_face(reference_bytes, probe_bytes)
```

If the application needs HTTP access, add a separate authenticated endpoint:

```text
POST /v1/face/verify
```

Request fields:

- authenticated user identity
- probe image upload
- reference-template identifier

Response fields:

- `matched`
- `similarity_score`
- `threshold`
- a non-sensitive verification attempt ID

Do not expose embeddings, raw image bytes, model paths, or internal user identifiers in API responses.

### Phase 2 — biometric safety controls

Before using real customer data, add:

1. Explicit opt-in consent before enrollment.
2. One-to-one verification only; do not add crowd or one-to-many identification.
3. Liveness detection to resist photo, replay, video, and screen spoofing.
4. Rate limits and lockouts for repeated failed verification attempts.
5. Calibrated thresholds based on consented evaluation data.
6. A deletion/revocation route that removes templates and related retained images.
7. Access controls, encryption, audit trails, and a documented retention period.

A failed liveness check, missing consent, or ambiguous/multiple faces must stop the flow rather than fall back to a payment attempt.

### Phase 3 — Fiuu sandbox integration

Use Fiuu's Hosted Payment Page first. The backend should:

1. Create an internal order with a unique idempotency key.
2. Complete app authentication, consent, liveness, and face verification.
3. Create a sandbox Hosted Payment Page redirect only after the checks succeed.
4. Send the customer to Fiuu to perform its own payment authentication.
5. Treat the browser return URL as a user-experience event only.
6. Mark an order paid only after a signed, server-to-server Fiuu notification is verified.
7. Store and process provider notifications idempotently to handle retries safely.

The application must never collect card details in this face-verification component. The Fiuu webhook handler must validate the provider signature before changing order state.

### Phase 4 — production readiness

Before production, complete a privacy, security, legal/compliance, accessibility, fraud, and biometric-performance review. Add monitoring, alerting, incident response, key rotation, reconciliation, disaster recovery, and a safe fallback for users who cannot or do not want to use face verification.

## Order-state model

A simple starting model:

```text
created
  → awaiting_verification
  → verification_failed | awaiting_checkout
  → payment_pending
  → paid | failed | cancelled
```

Only a verified Fiuu notification may transition `payment_pending` to `paid`.

## Test plan

Automate at least these cases before integrating a payment provider:

- same person, different images → match
- different people → no match
- zero faces, multiple faces, corrupt images → safe rejection
- consent missing, withdrawn, or expired → enrollment/verification blocked
- liveness failure → checkout blocked
- duplicate order ID → no duplicate provider request
- invalid/tampered webhook signature → order unchanged
- repeated valid webhook → idempotent result
- logs contain no raw image bytes, templates, secrets, or payment credentials

## Configuration

Keep local model paths in a local `.env` file. Keep production credentials in a secrets manager, not in `.env` files or Git.

Expected future provider configuration includes separate sandbox and production values, a public HTTPS notification URL, signature keys, and domain/IP allowlisting where required by the provider.

## Fiuu references

- [Fiuu merchant API specification](https://github.com/FiuuPayment/Documentation-Fiuu_API_Spec)
- [Fiuu Hosted Payment Page and notification guidance](https://github.com/FiuuPayment/Cheatsheet-BestPractices-Fiuu_API)
- [Fiuu PHP Hosted Payment SDK](https://github.com/FiuuPayment/SDK-Fiuu_PHP)

Fiuu integration details in this document were rephrased for compliance with licensing restrictions.
