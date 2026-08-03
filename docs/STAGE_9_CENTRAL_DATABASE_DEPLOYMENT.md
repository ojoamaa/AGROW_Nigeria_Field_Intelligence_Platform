# Stage 9 — Central PostgreSQL and QR Deployment

## Objective
Use one PostgreSQL database for local development, Render, agents and public farmer verification. This removes the “Invalid Farmer Record” result caused by separate SQLite databases.

## Render setup
1. Create a Render PostgreSQL database.
2. Copy its Internal Database URL into the web service environment variable `DATABASE_URL`.
3. Set `APP_BASE_URL` to the public Render web-service URL.
4. Set one strong `QR_SECRET_KEY`; use the exact same value locally.
5. Set `MINISTRY_INVITE_CODE=DATADEV`.
6. Set a new `AGROW_ADMIN_PASSWORD`.
7. Redeploy from GitHub.

## Local setup
Copy `.env.example` to `.env` and use the Render External Database URL for `DATABASE_URL`. Keep `QR_SECRET_KEY` identical to Render.

## Existing-record migration
Back up `agrow.db`, then run:

```bash
python scripts_migrate_sqlite_to_postgres.py
```

The migration is idempotent for users and farmers: existing IDs are skipped.

## Verification
Register a test farmer, download the new ID card, scan its QR from a phone, and confirm the public page shows the same farmer without login.

## Important storage note
PostgreSQL centralises records, agents, audit logs and coordinates. Local farmer photo files are not automatically cloud-persistent. Configure a Render persistent disk or object storage before field production.
