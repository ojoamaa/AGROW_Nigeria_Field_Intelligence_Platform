# AGROW - Agricultural Geographic Registration & Operations Workspace

This package is the Stage 8.1 recovery baseline for the AGROW digital agriculture platform. It preserves farmer registration, agent access, public farmer verification, signed QR identity, geolocation/geofence checks, distribution records, analytics and offline capture while aligning the product with the wider agricultural value chain.

AGROW is programme-independent. It can be used by farmers, cooperatives, agribusinesses, aggregators, development partners and government institutions across Nigeria, Africa and other agricultural markets.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Configuration

Copy `.env.example` to `.env` and configure:

- `APP_BASE_URL`: deployed public URL used by verification QR codes.
- `ORGANISATION_INVITE_CODE`: controlled agent-onboarding code.
- `QR_SECRET_KEY`: long random secret used to sign Farmer ID verification links.

## Stage 8.1 corrections

- AGROW repositioned as a platform and brand, not a World Bank project-specific application.
- Project-specific and ministry-only labels removed from the active interface.
- Organisation-based agent onboarding retained with backward compatibility.
- Farmer metrics replace beneficiary-only language.
- Farmer ID PDF generator repaired and rebuilt with a signed functional QR code.
- Existing registration, verification, geofence, distribution and analytics capabilities preserved.

See `docs/AGROW_PLATFORM_VISION.md` for the product scope.
