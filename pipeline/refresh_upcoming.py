"""Weekly refresh (GitHub Action): re-pull the upcoming edition's entrant lists and swap its rows
in data/public/runners.csv. Needs only committed files plus the GeoNames places file.

Stops without changing anything when there is no upcoming edition, race day has passed (run the
full pipeline locally then, to pull results), or a list comes back empty or much shorter than
before, which usually means the page changed rather than runners withdrew.
"""
import os
import sys
import time

import public
from common import BASE, snapshot_get
from geocode import geocode_row, load_overrides, load_places
from parse import parse_entrants

# A drop larger than this fraction since the last refresh is treated as a broken page.
MAX_DROP = 0.5


def warn(msg):
    # Shows as an annotation on the GitHub Actions run; plain output when run locally.
    prefix = "::warning::" if os.environ.get("GITHUB_ACTIONS") else "WARNING: "
    print(prefix + msg)


def main():
    up = public.load_upcoming()
    if not up:
        print("No upcoming edition in upcoming.json; nothing to refresh.")
        return
    today = time.strftime("%Y-%m-%d")
    if today > up["race_date"]:
        warn(f"{up['year']} race day ({up['race_date']}) has passed. Run ./pipeline/run_all.sh locally "
             "to pull results; the weekly refresh no longer updates it.")
        return

    rows = []
    for dist, did in up["dids"].items():
        html, _ = snapshot_get(f"{BASE}/entrants_event.aspx?did={did}", f"entrants_{did}", refresh=True)
        rows += parse_entrants(html, up["year"], dist, did)

    year = str(up["year"])
    current = [r for r in public.read_runners() if r["year"] != year]
    before = sum(1 for r in public.read_runners() if r["year"] == year) + up.get("unmapped", 0)
    if not rows or len(rows) < before * (1 - MAX_DROP):
        warn(f"{year} entrant lists returned {len(rows)} rows (was {before}); leaving data unchanged.")
        sys.exit(1)

    places, overrides = load_places(), load_overrides()
    mapped, unmapped = [], []
    for r in rows:
        (mapped if geocode_row(r, places, overrides) else unmapped).append(r)
    for r in unmapped:
        warn(f"Unrecognized hometown for a {year} {r['distance']} registrant: {r['city']!r}, {r['state']!r}. "
             "Add it to data/manual_geocode.csv.")

    past = public.read_past_keys()
    up["returning"] = sum(k in past for k in (public.hashed_keys([r]).pop() for r in rows))
    up["unmapped"] = len(unmapped)
    up["as_of"] = today
    public.write_runners(current + mapped)
    public.save_upcoming(up)
    print(f"{year}: {len(rows)} registered ({len(unmapped)} unmapped), {up['returning']} returning, as of {today}")


if __name__ == "__main__":
    main()
