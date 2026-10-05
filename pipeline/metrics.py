"""Step 5: per year x distance metrics -> data/metrics.csv, plus repeat-runner summary.

Entrants = everyone in the results (finished + DNF + DNS); starters exclude DNS.
"""
import csv
import statistics
from collections import defaultdict

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
    rows = list(csv.DictReader(open(DATA / "runners_geo.csv")))
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
        w = csv.DictWriter(f, list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    for m in out:
        print(m)

    # Repeat runners, keyed on UltraSignup participant_id (fallback: name).
    years = defaultdict(set)
    region_of = {}
    for r in rows:
        key = r["participant_id"] or f"{r['first']} {r['last']}".lower()
        years[key].add(r["year"])
        region_of[key] = r["region"]
    repeats = {k: v for k, v in years.items() if len(v) > 1}
    print(f"\nunique runners: {len(years)}, repeat (2+ years): {len(repeats)}")
    by_region = defaultdict(int)
    for k in repeats:
        by_region[region_of[k]] += 1
    print("repeat runners by region:", dict(by_region))


if __name__ == "__main__":
    main()
