# AGROW Pilot Production Readiness

## One-time transition from an older replaceable folder

Before replacing the current `AgrowNova_2026_Production` folder, run
`MIGRATE_CURRENT_DATA.bat` from that current folder. It moves the local SQLite
file, uploads and queue into `%USERPROFILE%\AGROW_DATA`.

After this transition, later source-folder replacements do not require new agent
or farmer registration because all local releases reuse the stable data folder.

## One-time phone access setup

Right-click `SETUP_WINDOWS_FIREWALL.bat` and select **Run as administrator**.
This permits inbound private-network traffic to TCP port 8501.

Windows must classify the Wi-Fi connection as **Private**, and the phone and
laptop must be on the same Wi-Fi without client isolation.

## Start local pilot

Double-click `run_app.bat`. The terminal prints:

- Laptop URL: `http://localhost:8501`
- Phone URL: `http://<laptop-LAN-IP>:8501`

Open the printed phone URL manually before scanning a Farmer ID QR. Keep the
terminal open while testing.

## Production deployment

For Render, retain:

- `APP_BASE_URL=https://<service>.onrender.com`
- `DATABASE_URL=<Render PostgreSQL URL>`
- `QR_SECRET_KEY=<permanent signing key>`
- `ORGANISATION_INVITE_CODE=<private code>`

Render start command:

`streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`

Commit and push to GitHub; Render then deploys the commit. Generate the final
public pilot Farmer ID only after deployment so its QR uses the public Render URL.
