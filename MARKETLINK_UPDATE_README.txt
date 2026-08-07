AGROW v4.3 MARKETLINK PILOT — INCREMENTAL UPDATE

Apply this update to the current working AgrowNova_GitHub repository only.
Do not replace .git, .env, agrow.db, uploads, or existing production data.

Changed/new files:
- app.py
- core/db.py
- services/market_service.py
- docs/MARKETLINK_V4_3_PILOT.md
- CHANGELOG.md

After copying the files:
1. Start AGROW locally. init_db() creates the new MarketLink tables automatically.
2. Log in with the working agent/admin account.
3. Open the new MarketLink tab.
4. Create one Poultry listing for a Verified farmer.
5. Create a Maize or Rice listing using the exact same form to confirm commodity independence.
6. Log out and expand MarketLink on the public landing page.
7. Test filters, Verify Farmer, seller contact, buyer enquiry and Market Price Board.
8. Create one agricultural input product and confirm it appears publicly.
9. Only after local acceptance, git add/commit/push to GitHub and deploy to Render.

No migration script is required for the three new tables; core/db.py creates them in both SQLite and PostgreSQL at application startup.
