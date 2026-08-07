# AGROW v4.3 — MarketLink Pilot

MarketLink is a universal agricultural marketplace layer on the existing AGROW farmer identity and operations platform. Poultry is the first demonstration commodity, but the data model and interface support all commodities without commodity-specific feature development.

## Added in this pilot

- Public MarketLink browser on the AGROW landing page.
- Produce listings tied to verified AGROW Farmer IDs.
- Generic commodity, product/variety, quantity, unit, asking price, ready date and location fields.
- Direct seller contact and signed farmer verification from each listing.
- Buyer enquiry capture.
- Agricultural input supplier/product listings with applicable commodities.
- Public input search.
- Market price board calculated from live produce listings.
- Authenticated MarketLink workspace for creating and managing listings.
- PostgreSQL/SQLite-compatible tables: `market_listings`, `input_products`, `market_enquiries`.

## Pilot acceptance test

1. Deploy the current code and allow `init_db()` to create the new MarketLink tables.
2. Log in as an agent or administrator.
3. Ensure at least one farmer has NIN status `Verified`.
4. Open MarketLink → Create Produce Listing.
5. Publish a Poultry listing (for example Broiler Chicken), then a second commodity such as Maize or Rice using the same form.
6. Log out and open the public MarketLink section on the landing page.
7. Filter and locate the listing.
8. Open Verify Farmer and confirm the signed AGROW verification profile.
9. Test Contact Seller / buyer enquiry.
10. Create an agricultural input listing and confirm it is visible publicly.
11. Confirm the Market Price Board reflects current produce listings.

## Deliberately deferred

Payments, escrow, logistics, order fulfilment, ratings, supplier verification tiers, warehouse/aggregation workflows and formal commodity-exchange price feeds are not part of this first MarketLink pilot.
