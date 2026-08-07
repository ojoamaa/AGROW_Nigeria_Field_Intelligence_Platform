# AGROW v4.3.1 — MarketLink Seller Contact

This increment improves seller contact without changing the existing farmer registry or MarketLink database schema.

## Added
- WhatsApp deep link using `wa.me`
- WhatsApp Web fallback for desktop browsers
- Direct phone dial link (`tel:`)
- Farmer profile panel with verification status, Farmer ID, primary crop and location
- Farmer photo preview when the photo file is available on the running server
- Farm-location link to Google Maps when valid latitude/longitude exists
- Verified farmer record link using the existing signed AGROW QR verification route
- Buyer enquiry upgraded to capture optional organisation/business and preferred delivery/collection date

## Database impact
No migration is required. Organisation and preferred date are stored inside the existing enquiry message field for this pilot increment.

## Test checklist
1. Open MarketLink > Buy Produce.
2. Expand Contact Seller.
3. Test WhatsApp. If the network blocks `wa.me`, test WhatsApp Web.
4. Test Call Seller on a phone.
5. Open View Farmer Profile and verify identity/location fields.
6. If GPS exists, test View Farm Location.
7. Submit Request Quote / Buyer Enquiry and confirm it appears under Manage > Buyer Enquiries for admin.
