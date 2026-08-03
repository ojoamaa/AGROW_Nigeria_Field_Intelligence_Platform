# AGROW Stage 8.3 Stabilisation

## Invite-code behaviour
The application accepts `ORGANISATION_INVITE_CODE` as the preferred setting and
continues to accept `MINISTRY_INVITE_CODE` for existing installations. When
neither variable exists during local development, the fallback is `DATADEV`.

After editing `.env`, stop Streamlit completely and restart it. Streamlit does
not reliably reload environment variables while the process is still running.

## Local test
1. Confirm `.env` contains `ORGANISATION_INVITE_CODE=DATADEV`.
2. Stop Streamlit with Ctrl+C.
3. Start with `python -m streamlit run app.py`.
4. Create an agent using `DATADEV`.
5. Register a new test farmer.
6. Generate and scan that farmer's QR.

## Production
Set the same variables in Render Environment. Do not commit `.env`.
