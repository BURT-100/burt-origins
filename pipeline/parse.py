"""Step 3: parse raw results JSON into data/runners.csv (one row per entrant).

UltraSignup status codes observed (inferred from place/time fields):
  1 = finished, 6 = finished (older events use 6), 2 = DNF, 3 = DNS.
Entrant pages (entrants_event.aspx) are empty once a race is over, but the
results JSON includes DNS rows, so it doubles as the entrant list.
"""
import csv
import json

from common import RAW, ROOT

STATUS = {1: "finished", 6: "finished", 2: "DNF", 3: "DNS"}
FIELDS = ["year", "distance", "did", "participant_id", "first", "last", "city", "state",
          "age", "gender", "status", "place", "time"]


def main():
    dids = json.loads((ROOT / "dids.json").read_text())
    rows = []
    for year, by_dist in dids.items():
        for dist, did in by_dist.items():
            for r in json.loads((RAW / f"results_{did}.json").read_text()):
                status = STATUS.get(r["status"], f"unknown_{r['status']}")
                rows.append({
                    "year": int(year), "distance": dist, "did": did,
                    "participant_id": r.get("participant_id") or "",
                    "first": (r.get("firstname") or "").strip(),
                    "last": (r.get("lastname") or "").strip(),
                    "city": (r.get("city") or "").strip(),
                    "state": (r.get("state") or "").strip().upper(),
                    "age": r.get("age") or "",
                    "gender": r.get("gender") or "",
                    "status": status,
                    "place": r["place"] if status == "finished" else "",
                    "time": (r.get("formattime") or "").strip() if status == "finished" else "",
                })
    rows.sort(key=lambda r: (r["year"], r["distance"], r["status"] != "finished",
                             r["place"] or 0, r["last"]))
    with open(ROOT / "data" / "runners.csv", "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> data/runners.csv")


if __name__ == "__main__":
    main()
