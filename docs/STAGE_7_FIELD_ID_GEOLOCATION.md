# Stage 7 — Farmer ID and Automatic Geolocation

Each farmer receives a downloadable PDF Farmer ID card containing a signed individual QR code.

A QR generated with `localhost` only works on the same computer. Production QR codes must use the deployed HTTPS URL configured through `APP_BASE_URL`.

The registration form now captures the field device GPS position after the agent grants browser location permission. Coordinates are automatically populated and remain editable. Records cannot be submitted with both coordinates at zero.

Analytics now groups farmers by State, LGA and Community and calculates farmer count, total land area and cluster centre coordinates for input distribution and aid planning.
