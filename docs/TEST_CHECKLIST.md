# Stage 1 Local Test Checklist

Record PASS or FAIL beside every item before committing the checkpoint.

## Startup
- [ ] `pip install -r requirements.txt` completes.
- [ ] `python -m streamlit run app.py` opens the application.
- [ ] No terminal traceback appears during startup.

## Authentication
- [ ] Admin login succeeds using the existing baseline credentials.
- [ ] Agent login succeeds.
- [ ] Invalid credentials are rejected.
- [ ] Logout returns to the login page.
- [ ] Password change works and the new password works after logout.

## Approved interface
- [ ] Fonts match the preferred GitHub version.
- [ ] Dashboard spacing and tab alignment are unchanged.
- [ ] Sidebar width and content are unchanged.
- [ ] Mobile layout remains usable.

## Farmer workflow
- [ ] Farmer registration form opens.
- [ ] State and LGA selection works.
- [ ] Required validation messages work.
- [ ] A test farmer saves successfully.
- [ ] The new farmer appears on the dashboard and analytics.
- [ ] Duplicate-today protection works.
- [ ] Photo capture/upload works.

## Operations
- [ ] Distribution page loads and filters records.
- [ ] Analytics charts load.
- [ ] Agent list loads.
- [ ] Farmer ID card/QR generation works.
- [ ] Offline queue page loads and sync can be tested safely.
