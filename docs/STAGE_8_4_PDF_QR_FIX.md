# AGROW Stage 8.4 - Farmer ID PDF and Local QR Fix

## Corrections

- Farmer ID Preview now downloads a real PDF ID card, not a PNG QR sheet.
- The PDF layout uses the approved CR80 sample design with farmer photo, details and signed QR.
- During local testing, a localhost APP_BASE_URL is automatically converted to the laptop LAN IP for QR generation.
- run_app.bat and run_app.sh bind Streamlit to 0.0.0.0 so a phone on the same Wi-Fi can reach the verification page.
- Production deployments continue to use the configured public APP_BASE_URL unchanged.

## Local test

1. Connect laptop and phone to the same Wi-Fi.
2. Start with run_app.bat.
3. Allow Python through Windows Firewall on Private networks if prompted.
4. Register a new farmer.
5. Open Farmer ID Preview and download Farmer ID Card (PDF).
6. Scan the QR from the PDF.

The QR should use a 192.168.x.x or 10.x.x.x address locally, not localhost.
