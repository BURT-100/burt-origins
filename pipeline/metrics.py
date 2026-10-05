"""Step 6: per year x distance metrics from data/public/runners.csv -> data/metrics.csv.

Entrants = everyone in the results (finished + DNF + DNS); starters exclude DNS.
"All" years covers completed editions only; an upcoming edition (registered so far)
gets its own rows but stays out of the totals.
"""
import csv
import statistics
from collections import defaultdict

import public
from common import ROOT

DATA = ROOT / "data"
REGIONS = ["Bainbridge Island", "Kitsap County", "King County", "Other WA", "Out of state"]


def summarize(rows):
    n = len(rows)
    mi = [float(r["miles"]) for r in rows if r["miles"]]
    out = {"n": n, "starters": sum(r["status"] != "DNS" for r in rows),
           "finishers": sum(r["status"] == "finished" for r in rows)}
    for reg in REGIONS:
        out[f"pct_{reg.lower().replace(' ', '_')}"] = round(100 * sum(r["region"] == reg for r in rows) / n, 1)
    out["median_miles"] = round(statistics.median(mi), 1) if mi else ""
    out["max_miles"] = max(mi) if mi else ""
    out["towns"] = len({(r["geo_city"], r["geo_state"]) for r in rows})
    return out


def main():
    rows = public.read_runners()
    up = public.load_upcoming()
    upcoming_year = str(up["year"]) if up else None
    groups = defaultdict(list)
    for r in rows:
        for dist in (r["distance"], "All"):
            groups[(r["year"], dist)].append(r)
            if r["year"] != upcoming_year:
                groups[("All", dist)].append(r)
    order = {"55K": 0, "110K": 1, "100M": 2, "All": 3}
    out = []
    for (year, dist), g in sorted(groups.items(), key=lambda kv: (kv[0][0], order[kv[0][1]])):
        out.append({"year": year, "distance": dist, **summarize(g)})
    with open(DATA / "metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(out[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    for m in out:
        print(m)
    print("repeats:", (public.PUBLIC / "repeats.json").read_text().strip())


if __name__ == "__main__":
    main()
