# AgrowNova User Guide — Recovery Baseline

## Starting the application
1. Open the AgrowNova project folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Run `pip install -r requirements.txt` once.
4. Run `python -m streamlit run app.py`, or double-click `run_app.bat` on Windows.
5. Open the local address shown in the terminal, normally `http://localhost:8501`.

## Administrator workflow
Log in from the landing page. The administrator can access Dashboard, Farmer Registration, Distribution, Analytics and Agents. Use Logout when finished. Change the default password before any live demonstration or deployment.

## Agent workflow
An authorised agent can sign up using the organisation invitation code, receive an assigned Agent ID, log in, register farmers and update their password.

## Farmer registration
Open **Farmer Registration**, complete the identity, location, farm, input, verification and photo fields, then submit. Verify that the success message appears and that the farmer is visible on the dashboard.

## Data protection
Do not commit `.env`, database files or real NIN records to GitHub. Use demonstration data in the public repository. Production data must be stored in protected persistent infrastructure.
