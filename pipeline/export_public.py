"""Step 5 (local): write the name-free public data from data/runners_geo.csv.

Writes data/public/{runners.csv, repeats.json, past_keys.txt} and adds `returning` and
`unmapped` to upcoming.json. Rows whose hometown couldn't be geocoded are left out of the
public rows: an error for completed editions, a count (`unmapped`) for the upcoming one.
"""
import csv
import json
from collections import defaultdict

import public
from common import ROOT


def main():
    rows = list(csv.DictReader(open(ROOT / "data" / "runners_geo.csv")))
    up = public.load_upcoming()
    up_year = str(up["year"]) if up else None
    done = [r for r in rows if r["year"] != up_year]
    upcoming = [r for r in rows if r["year"] == up_year]

    unmatched_done = [r for r in done if not r["miles"]]
    if unmatched_done:
        raise SystemExit(f"{len(unmatched_done)} completed-edition rows are unmatched; "
                         "fix them in data/manual_geocode.csv first")
    public.write_runners([r for r in rows if r["miles"]])

    # Repeat runners across completed editions.
    years, region_of = defaultdict(set), {}
    for r in done:
        k = public.runner_key(r)
        years[k].add(r["year"])
        region_of[k] = r["region"]
    by_region = defaultdict(int)
    for k, v in years.items():
        if len(v) > 1:
            by_region[region_of[k]] += 1
    repeats = {"unique": len(years), "repeat": sum(by_region.values()), "byRegion": dict(sorted(by_region.items()))}
    (public.PUBLIC / "repeats.json").write_text(json.dumps(repeats, indent=2) + "\n")

    past = public.hashed_keys(done)
    public.write_past_keys(past)
    if up:
        up["returning"] = sum(k in past for k in (public.hashed_keys([r]).pop() for r in upcoming))
        up["unmapped"] = sum(1 for r in upcoming if not r["miles"])
        public.save_upcoming(up)
    print(f"public: {sum(1 for r in rows if r['miles'])} rows, {len(past)} past runners, repeats {repeats}")


if __name__ == "__main__":
    main()
