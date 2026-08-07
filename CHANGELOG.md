# AGROW Changelog

## v4.3.1 — MarketLink Seller Contact
- Added WhatsApp and WhatsApp Web seller contact options.
- Added direct call link for mobile users.
- Added farmer profile and signed verification access from listings.
- Added farm map link when farmer GPS coordinates are available.
- Expanded buyer enquiry with organisation and preferred delivery date without a schema migration.


## v4.3 MarketLink Pilot
- Added universal produce marketplace tied to verified AGROW Farmer IDs.
- Added agricultural input marketplace and supplier listings.
- Added public produce/input discovery and direct seller contact.
- Added signed farmer verification link from market listings.
- Added buyer enquiry capture and listing status management.
- Added live listing-derived market price board.
- Added PostgreSQL/SQLite MarketLink tables without changing the v4.2 farmer identity schema.
# Stage 8.1 — Platform Brand Alignment
- Repositioned AGROW as Agricultural Geographic Registration & Operations Workspace, independent of any single project or donor.
- Removed World Bank/project-prototype language from the active application.
- Replaced ministry-only agent onboarding language with organisation onboarding while preserving backward compatibility.
- Reframed beneficiary metrics as registered farmer metrics.
- Added the AGROW platform vision and value-chain product pillars.

# Changelog

## Stage 5 — Fast Farmer Registration

- Isolated Farmer Registration with `st.fragment`.
- Field interactions now rerun only the registration section instead of the full dashboard.
- Retained Sections 1–11 in sequence.
- Retained one full application refresh after a successful database commit so Distribution, Analytics and Admin totals remain current.
- Retained clean-form reset and Farmer ID confirmation.


## Recovery Stage 1 — 2026-07-30
- Restored the GitHub repository as the single source of truth.
- Preserved the approved interface and navigation.
- Corrected non-visual configuration conflicts and database seed indentation.
- Added environment configuration, startup scripts, audit documentation, user guide, GitHub workflow and test checklist.

## Recovery Stage 2 — Agent Authentication Fix
- Set local ministry invite code to DATADEV.
- Generate visible state-prefix usernames such as KN-01 and FC-01.
- Added password confirmation and minimum-length validation.
- Normalize login usernames and passwords before authentication.
- Verify newly registered credentials immediately after database insertion.
- Save the captured agent photo under uploads/agents.
- Keep the generated username visible after registration.

## Stage 3 — Registration Performance (2026-07-31)
- Removed forced full-application rerun after farmer submission.
- Farmer save confirmation and Farmer ID now appear immediately.
- Enabled SQLite WAL mode, normal synchronous writes and a busy timeout.
- Updated deprecated Streamlit `use_container_width` arguments to `width`.
- Preserved the approved user interface and registration workflow.


## Recovery Stage 4 — Sequential Registration and Clean Reset
- Reordered farmer registration into Sections 1 through 11.
- Moved support delivery and camera capture into their correct sequence.
- Added review confirmation before submission.
- Clears all fields, selected inputs and captured photo after a successful save.
- Retains validation entries when submission fails.
- Displays the save confirmation and Farmer ID above the new blank form.

## Stage 6 — AGROW product alignment
- Expanded AGROW as Agricultural Geographic Registration & Operations Workspace.
- Promoted public farmer verification to the landing page.
- Added Farmer Verification workspace for agents and administrators.
- Added signed individual Farmer QR generation and download in Farmer ID Preview.
- Distinguished platform-access QR from individual farmer verification QR.
- Preserved role-restricted agent operations and ministry analytics.

## Stage 8.3 — Stabilisation Release (2026-08-03)
- Added one canonical invite-code resolver.
- Preferred `ORGANISATION_INVITE_CODE`; retained `MINISTRY_INVITE_CODE` compatibility.
- Normalised invite codes with whitespace trimming and case-insensitive comparison.
- Restored a functional local development `.env` using `DATADEV`.
- Added explicit restart guidance when an invite code fails.
- Preserved PostgreSQL/SQLite selection and signed QR verification from Stage 8.2.
