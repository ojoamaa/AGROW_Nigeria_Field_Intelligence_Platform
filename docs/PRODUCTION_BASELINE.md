# AgrowNova Production Baseline v1

This release is based only on the verified `AgrowNova_2026` folder.

## Production rules

- PostgreSQL is mandatory on Render.
- SQLite is only a local fallback.
- Demo users and farmers are disabled unless `AGROW_ENABLE_DEMO_DATA=true`.
- `.env`, `*.db`, credentials, and Python caches must never be committed.
- New Farmer QR codes use a record-specific verification token stored in PostgreSQL.
- Legacy HMAC QR codes remain readable when the same `QR_SECRET_KEY` is configured.

## Release acceptance test

1. Admin login succeeds.
2. Agent signup produces a usable username.
3. Agent login succeeds.
4. Farmer registration saves to PostgreSQL.
5. Admin sees the new farmer.
6. Farmer ID and named QR download correctly.
7. QR scan on a phone returns Farmer Verified.
8. Custom programme inputs/services can be added during registration.
