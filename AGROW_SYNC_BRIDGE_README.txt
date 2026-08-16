AGROW v4.5 — FIELD-TO-CENTRAL SYNC BRIDGE
==========================================

PURPOSE
This refinement separates device-local offline work from the central AGROW database correctly.

EXPECTED FLOW
1. Agent opens AGROW Field on phone/tablet.
2. Agent can register a farmer while offline.
3. Farmer is stored on that device as PENDING.
4. When connectivity returns, AGROW Field automatically attempts a secure sync.
5. The manual "Sync Pending Records" button remains available for controlled retry.
6. During transfer the device status becomes SYNCING.
7. Central AGROW validates the agent, territory and GPS and inserts the farmer into the central farmers table.
8. Central server writes a field_sync_receipts audit record.
9. Device changes the record to SYNCED, or FAILED with an error message.
10. Main AGROW dashboard reads server receipts; it does NOT pretend to see unsynced records that still exist only on a phone.

FILES IN THIS BUNDLE
- app.py                              Main AGROW replacement with corrected Central Sync Monitor
- field_api.py                        AGROW Field HTTPS/PWA API with sync receipt audit trail
- agrow_field/static/app.js           Device queue + automatic reconnect sync + PENDING/SYNCING/SYNCED/FAILED states
- agrow_field/static/sw.js            Cache version bumped so installed devices receive this build
- remaining agrow_field/static files  Existing camera/GPS/PWA interface retained
- requirements_field.txt
- render.yaml

IMPORTANT DATABASE RULE
The deployed AGROW Field service MUST use the SAME production DATABASE_URL as the main AGROW service.
That is what makes a phone sync write directly to the central AGROW farmer registry.
Do not point the deployed Field service at a separate local SQLite file.

LOCAL REPLACEMENT
From your AgrowNova_GitHub root:
1. Back up the current working folder or commit the current checkpoint first.
2. Replace app.py with the app.py in this bundle.
3. Replace field_api.py with the field_api.py in this bundle.
4. Replace the agrow_field folder with the agrow_field folder in this bundle.
5. Keep your existing core/, services/, database configuration and other production files.

LOCAL TEST — MAIN AGROW
python -m streamlit run app.py
Open http://localhost:8501
Confirm login and normal dashboard still work.

LOCAL TEST — FIELD APP
In a second Anaconda Prompt from the same project folder:
python -m uvicorn field_api:app --host 0.0.0.0 --port 8000
Laptop: http://127.0.0.1:8000
LAN test: http://YOUR-LAPTOP-IP:8000

NOTE ABOUT LOCAL TESTING
A local field_api.py normally uses whatever database core/db.py resolves locally. Therefore a local sync test may write to your local AGROW database. The production proof must be done against the deployed HTTPS AGROW Field service using the SAME production DATABASE_URL as the main AGROW service.

RENDER DEPLOYMENT
Create/retain AGROW Field as a separate Web Service. Do not replace the Streamlit service.
Build command:
  pip install -r requirements_field.txt
Start command:
  python -m uvicorn field_api:app --host 0.0.0.0 --port $PORT
Health check:
  /api/field/health

Required environment variables:
  DATABASE_URL       = SAME PostgreSQL URL used by the main AGROW service
  FIELD_API_SECRET   = strong random secret
  QR_SECRET_KEY      = existing value only if intentionally used as fallback

PHONE INSTALL / PRODUCTION TEST
1. Open the deployed AGROW Field HTTPS URL in Chrome on Android.
2. Log in once while online.
3. Allow Camera and Location.
4. Chrome menu > Install app / Add to Home screen.
5. Open AGROW Field from the installed icon.
6. Turn mobile data/Wi-Fi off.
7. Register a farmer and save offline.
8. Confirm PENDING = 1.
9. Restore connectivity.
10. Wait a few seconds. AGROW Field will automatically attempt synchronization.
11. If needed, tap Sync Pending Records once.
12. Confirm the device record changes to SYNCED.
13. Open the main AGROW workspace and confirm the farmer appears in Recent Farmer Registrations.
14. In Central Sync Monitor, confirm a server receipt exists for the same Farmer ID.

CENTRAL MONITOR INTERPRETATION
- A phone's PENDING count is device-local and cannot be truthfully displayed by the server before transmission.
- Field Records Received = successful device sync receipts received by the central server.
- Field Sync Failed = attempts that reached the server but failed validation/insertion.
- Main Workspace Local Queue = only records queued by the Streamlit application itself.

RELEASE CHECK
Do not call the mobile/offline build production-ready until this exact end-to-end test passes:
PHONE OFFLINE -> LOCAL PENDING -> RECONNECT -> FIELD SYNC -> CENTRAL RECEIPT -> FARMER IN CENTRAL REGISTRY.
