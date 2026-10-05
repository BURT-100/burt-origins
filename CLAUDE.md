# BURT 100 — Runner Origin Map

## Goal
Build an interactive map showing where BURT 100 runners travel from, year by year
(2022?–2026), broken down by distance (55K / 110K / 100M). Inspired by the iRunFar
article "Ultrarunning Growth in the U.S. Through a Geographic Lens"
(https://irunfar.com/ultrarunning-growth-in-the-u-s-through-a-geographic-lens).

Race: BURT 100, Bainbridge Island, WA (start/finish Battle Point Park), held each February.
Fields are small (~20–60 runners/year), so a national map is the wrong default.

## Data source: UltraSignup (no official API — undocumented endpoints)
Each year × distance has its own `did` (distance ID).

- Results JSON: `https://ultrasignup.com/service/events.svc/results/{did}/1/json?_search=false`
  (the older `/results/{did}/json` path now returns "Endpoint not found"). Includes city/state and DNF/DNS rows.
  Status codes: 1 and 6 = finished, 2 = DNF, 3 = DNS.
- Entrants (server-rendered HTML): `https://ultrasignup.com/entrants_event.aspx?did={did}`
  - Entrant table historically the 3rd `<table>`; columns include age, first, last, city, state, bib.
- Runner history: `https://ultrasignup.com/service/events.svc/historybyname/{first}/{last}/`

All dids are discovered and saved in `dids.json` (2023 was 55K-only; no earlier years on UltraSignup).
Entrant pages are empty after the race, so the results JSON serves as the entrant list.
Upcoming edition (no results yet): `discover.py` follows the registration page (`register.aspx?eid=17000`,
which always shows the current edition) and writes `upcoming.json` (year, race date, dids, caps).
Its entrant lists are saved as dated snapshots (`entrants_{did}_{YYYY-MM-DD}.html`) and re-fetched only
with `--refresh`; this is the one exception to "never re-fetch". Never request results JSON for the
upcoming edition, or an empty result would be cached forever.
Known `dtid` values: 2023 = 54846, 2026 = 63528.

Rules: low request rate (sleep ≥2s), cache raw responses to disk, never re-fetch cached data.
Endpoints are undocumented and may change — inspect actual JSON fields before parsing;
don't assume field names.

## Pipeline
1. **Discover** all dids for every year × distance; write `dids.json`.
2. **Fetch** results JSON + entrants HTML per did into `data/raw/`.
3. **Parse** into one tidy CSV: year, distance, first, last, city, state, age, gender, status
   (finished/DNF/DNS if available), time. Note which years have entrant lists vs finishers only.
4. **Geocode** city/state offline using a US city centroid dataset (e.g., SimpleMaps free US
   cities or GeoNames). Log unmatched rows for manual fixes; don't silently drop them.
5. **Metrics** per year × distance: n, % Bainbridge Island, % Kitsap County, % King County,
   % other WA, % out of state, median and max travel distance (great-circle miles from
   Battle Point Park), count of distinct origin towns.
6. **Map**: single self-contained HTML page (Leaflet or MapLibre).
   - Default view zoomed to Puget Sound; small US inset or "zoom out" for far travelers.
   - Year slider + distance toggle (55K / 110K / 100M / All).
   - Origin points (size by count) with optional lines to the race start.
   - Stats panel showing the metrics for the current filter.
   - Show runner counts by town, not individual names, in the public version.

## Questions to explore once data is in
- Is the field getting more or less local as the race grows (cap went ~30 → 65)?
- Do longer distances draw from farther away (iRunFar found ~2× travel for 100M vs 50K)?
- How many repeat runners year to year, and are they mostly local?

## Owner
Greg — lives on Bainbridge Island, iOS developer, comfortable with Python/JS.
Prefers direct, practical communication.
