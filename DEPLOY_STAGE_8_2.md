# AGROW Stage 8.2 — PostgreSQL Farmer Verification Hotfix

## Root cause fixed
The previous application accepted `DATABASE_URL` in Render but `core/db.py` always opened a local SQLite file. Render redeploys can erase that temporary file, so a QR signature could be valid while the farmer record no longer existed.

Stage 8.2 uses PostgreSQL whenever `DATABASE_URL` is set and falls back to SQLite only for local development without `DATABASE_URL`. Registration and public QR verification now read/write the same persistent database.

## Deployment
1. Back up the current production folder and database.
2. Replace application source with this package; do not overwrite `.env` blindly.
3. Keep `DATABASE_URL`, `APP_BASE_URL`, `MINISTRY_INVITE_CODE`, and `QR_SECRET_KEY` in Render Environment.
4. Deploy. Tables are created automatically.
5. Register one NEW test farmer on the deployed Render app, generate the ID, and scan its QR.

## Existing test Farmer ID
A farmer registered before this hotfix may have existed only in Render's temporary SQLite file and may already be lost after redeployment. Such a record must be imported from a backup/CSV or registered again. The QR cannot verify a record that is absent from PostgreSQL.
