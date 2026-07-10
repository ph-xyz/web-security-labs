# Solution

1. Capture Alice's cookie and bearer token and configure them in Autorize.
2. Browse the application as Bob or Root and compare the repeated responses.
3. Validate the following authorization failures:

- `GET /api/v1/admin/users` — BFLA
- `/api/v1/projects/*`, `/documents/*`, `/invoices/*` — BOLA
- `POST /api/v1/admin/users/bob/suspend` — BFLA
- `GET /api/v1/reports/RPT-B-777/export` with `X-Org-ID: org-beta`
- `GET /api/v2/billing/invoices/INV-B-900` — BOLA
- `POST /api/v2/projects/PROJ-B-900/rotate-secret` — BFLA
- GraphQL `GetTicket` with `TCK-B-2` — BOLA

Use the protected audit-log, refund and feature-flag endpoints as control cases.
