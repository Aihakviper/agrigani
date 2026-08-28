# Known Issues and Roadmap

## P0: blocks a reliable release

### Frontend conflict markers

Twelve frontend files contain committed conflict markers and duplicate
implementations. The remote `Frontend` branch has the same problem and has no
unique commits beyond `main`.

Required action: create a new cleanup branch from `mvp-development`, choose the
intended implementation in each file, preserve current API/auth behaviour, and
perform browser smoke tests.

### Public vendor and disease writes

`DiseaseViewSet` and `VendorViewSet` are full `ModelViewSet` classes with
`AllowAny`. Anonymous callers can potentially create, edit, verify, rate, or
delete records.

Required action: make public access read-only and restrict writes to authorized
admins or verified vendor owners.

## P1: MVP reliability

- Add automated end-to-end tests for authentication, diagnosis, history, and
  vendor referrals.
- Restore explicit image-quality and unsupported-image rejection policies if
  they are still product requirements; they are absent from the current branch.
- Stop returning raw exception details from diagnosis failures.
- Replace wildcard FastAPI CORS configuration.
- Validate downloaded image URLs against an allowlist to reduce SSRF risk.
- Replace the hard-coded `~90%` model-info value with versioned evaluation
  metadata.
- Add a confidence/rejection policy validated on an independent field dataset.

## Model findings

The current 22-class held-out evaluation reports 89.39% overall accuracy.
Tomato is the weakest crop at 77.14%, followed by maize at 85.75%.

Priority review groups:

- Maize leaf blight vs. maize leaf spot
- Tomato leaf blight vs. Septoria leaf spot
- Tomato leaf blight vs. Verticillium wilt
- Tomato leaf curl vs. Septoria leaf spot

Review labels, duplicates, leakage, class balance, and image quality before
focused retraining.

## Marketplace roadmap

The current vendor feature only selects up to five verified vendors in the
same region. It does not match products, calculate distance, check stock, or
record leads.

Recommended sequence:

1. Secure vendor writes and add vendor ownership.
2. Add Product and VendorProduct inventory.
3. Match products to treatment recommendations.
4. Add price, stock, WhatsApp, delivery, and last-updated fields.
5. Rank verified vendors by relevance, distance, availability, and rating.
6. Track calls/WhatsApp inquiries before building checkout.
7. Consider Paystack or Flutterwave only after validating transaction demand.

## Production readiness

- Use PostgreSQL rather than SQLite.
- Use managed object storage for diagnosis images.
- Set `DEBUG=False`, a strong secret, HTTPS, and explicit allowed hosts.
- Add Redis-backed throttling/caching for multi-instance deployment.
- Add monitoring, error tracking, backups, and data-retention rules.
