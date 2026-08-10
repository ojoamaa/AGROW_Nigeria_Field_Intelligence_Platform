# AGROW Field v1.0 — Offline Enumeration Companion

## Purpose
AGROW Field is a lightweight installable PWA for field agents. After one online login it caches the agent identity/territory and can register farmers without internet using IndexedDB, GPS and camera capture. Pending records sync to the existing AGROW PostgreSQL registry through `field_api.py` when internet returns.

## Local test
1. `pip install -r requirements_field.txt`
2. Set the same `DATABASE_URL` used by AGROW Web.
3. Set `FIELD_API_SECRET` to a strong private value.
4. Run `python -m uvicorn field_api:app --host 0.0.0.0 --port 8080`
5. Open `http://localhost:8080` on laptop. For phone/PWA installation use an HTTPS deployment.

## Hosted deployment
Deploy this repository as a second Render Web Service (for example `agrow-field`) using:
- Build: `pip install -r requirements_field.txt`
- Start: `uvicorn field_api:app --host 0.0.0.0 --port $PORT`
- Environment: `DATABASE_URL`, `FIELD_API_SECRET`, and optional `AGROW_TERRITORY_BOUNDS_JSON`

Both AGROW Web and AGROW Field must point to the same PostgreSQL database.

## Demonstration test
1. Login online as an existing AGROW agent.
2. Install/Add AGROW Field to Home Screen.
3. Turn off Wi-Fi/mobile data.
4. Register 2–3 farmers, capture GPS/photo, Save Farmer Offline.
5. Confirm Pending count rises.
6. Restore internet and tap Sync Pending Records.
7. Confirm records show SYNCED.
8. Open AGROW Web and verify the new farmers in the registry and QR/ID workflow.

## Important
This is an offline-first field capture layer, not a wrapper around Streamlit. The public verification, dashboard, MarketLink, input marketplace and market intelligence remain on AGROW Web.
