"""Step 6: per year x distance metrics from data/public/runners.csv -> data/metrics.csv.

Entrants = everyone in the results (finished + DNF + DNS) plus registrants; starters exclude DNS and registrants.
"All" years includes an upcoming edition's registrants (status "registered"), matching
the page's "All years" view.
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
    out = {"n": n, "starters": sum(r["status"] not in ("DNS", "registered") for r in rows),
           "finishers": sum(r["status"] == "finished" for r in rows)}
    for reg in REGIONS:
        out[f"pct_{reg.lower().replace(' ', '_')}"] = round(100 * sum(r["region"] == reg for r in rows) / n, 1)
    out["median_miles"] = round(statistics.median(mi), 1) if mi else ""
    out["max_miles"] = max(mi) if mi else ""
    out["towns"] = len({(r["geo_city"], r["geo_state"]) for r in rows})
    return out


def main():
    rows = public.read_runners()
    groups = defaultdict(list)
    for r in rows:
        for dist in (r["distance"], "All"):
            groups[(r["year"], dist)].append(r)
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
