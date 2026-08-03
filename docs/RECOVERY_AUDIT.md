# AgrowNova Recovery Audit — Stage 1

## Baseline
This package is derived directly from the GitHub `main` branch ZIP supplied on 30 July 2026. The approved Streamlit interface, typography, spacing, tabs, dashboard layout and navigation were intentionally preserved.

## Verification completed
- Confirmed `app.py` as the active entry point.
- Confirmed SQLite persistence through `core/db.py` and `services/*`.
- Confirmed farmer, user, offline queue, reporting, ID and logging modules are present.
- Confirmed the active Python files pass syntax compilation.
- Confirmed the GitHub project contains the approved UI assets and existing farmer images.

## Safe corrections in this checkpoint
- Removed one duplicate `qrcode` import.
- Made `APP_BASE_URL` configurable through `.env` without changing its current default.
- Removed conflicting duplicate upload-directory assignments in `core/config.py`.
- Ensured required data/upload directories are created consistently.
- Corrected indentation in the default-admin database seed block.
- Added run scripts, environment template, recovery documentation and test checklist.

## Risks not yet changed
These require controlled testing before modification:
- Passwords are currently stored and compared as plain text.
- Demo/default credentials are seeded automatically.
- SQLite persistence on Render requires a persistent disk or external database.
- Production secrets must not use fallback values.
- Full browser and end-to-end testing must be completed locally.

## Stage 1 acceptance condition
The project launches locally and the following work exactly as before: login, dashboard, farmer registration, distribution, analytics, agents, QR/ID functions and password change.
