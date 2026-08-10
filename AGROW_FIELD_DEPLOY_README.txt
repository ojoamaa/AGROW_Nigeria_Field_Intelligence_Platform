AGROW FIELD - DEPLOYMENT OVERLAY

PURPOSE
Deploy AGROW Field as a separate HTTPS/PWA service while leaving the existing AGROW Streamlit production service unchanged.

COPY INTO EXISTING AgrowNova_GitHub ROOT
- field_api.py
- agrow_field/ (entire folder)
- requirements_field.txt
- render.yaml (optional Blueprint support)

LOCAL TEST
python -m uvicorn field_api:app --host 127.0.0.1 --port 8000
Open: http://127.0.0.1:8000
Health: http://127.0.0.1:8000/api/field/health

GIT
Run git status first. Stage only the Field deployment files intentionally.
Suggested commit message:
AGROW Field PWA production deployment and offline sync

RENDER - CREATE A NEW WEB SERVICE
Do NOT replace the existing AGROW Streamlit service.
Build command:
pip install -r requirements_field.txt
Start command:
python -m uvicorn field_api:app --host 0.0.0.0 --port $PORT
Health check path:
/api/field/health

ENVIRONMENT VARIABLES
DATABASE_URL = same central PostgreSQL connection used by AGROW
FIELD_API_SECRET = strong random secret unique to Field API
QR_SECRET_KEY = existing value only if field tokens intentionally fall back to it
Also copy any environment variables required by core/db.py and services used by field_api.py.

PHONE INSTALL
After Render deployment opens successfully over HTTPS:
1. Open the AGROW Field Render URL in Chrome on Android.
2. Log in once while online and approve Camera + Location permissions.
3. Chrome menu -> Install app / Add to Home screen.
4. Open the installed AGROW Field icon.
5. Perform an online activation test, then an offline queue test, then reconnect and sync.

IMPORTANT
127.0.0.1 is laptop-only and cannot be installed from the phone.
Do not deploy until local Field form validation/camera/GPS/dropdowns pass.


CAMERA REFINEMENT (v3)
----------------------
The green photo button now uses the browser MediaDevices/getUserMedia camera API for genuine live capture.
It no longer relies on a file input with a capture hint. The separate gallery/file control remains as fallback.
For phone deployment, camera access requires HTTPS (Render provides HTTPS) and the user must allow Camera permission.
The service-worker cache name is bumped to agrow-field-v3-camera so installed devices fetch the new camera interface.
