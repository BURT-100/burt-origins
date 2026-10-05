"""Step 3: parse raw results JSON into data/runners.csv (one row per entrant).

UltraSignup status codes observed (inferred from place/time fields):
  1 = finished, 6 = finished (older events use 6), 2 = DNF, 3 = DNS.
Entrant pages (entrants_event.aspx) are empty once a race is over, but the
results JSON includes DNS rows, so it doubles as the entrant list.

The upcoming edition (upcoming.json) has no results yet; its rows come from the newest
entrant-list snapshot with status "registered", and its as-of date is written back to
upcoming.json.
"""
import csv
import json

from bs4 import BeautifulSoup

from common import RAW, ROOT, latest_snapshot

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
    up_path = ROOT / "upcoming.json"
    if up_path.exists():
        upcoming = json.loads(up_path.read_text())
        dates = []
        for dist, did in upcoming["dids"].items():
            snap = latest_snapshot(f"entrants_{did}")
            if not snap:
                continue
            dates.append(snap[1])
            rows += parse_entrants(snap[0].read_text(), upcoming["year"], dist, did)
        upcoming["as_of"] = min(dates) if dates else None
        up_path.write_text(json.dumps(upcoming, indent=2) + "\n")

    rows.sort(key=lambda r: (r["year"], r["distance"], r["status"] != "finished",
                             r["place"] or 0, r["last"]))
    with open(ROOT / "data" / "runners.csv", "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> data/runners.csv")


def parse_entrants(html: str, year: int, dist: str, did: int) -> list[dict]:
    """Rows from the server-rendered entrant table (columns located by header text)."""
    table = BeautifulSoup(html, "html.parser").find("table", id="ContentPlaceHolder1_gvEntrants")
    if table is None:
        return []
    trs = table.find_all("tr")
    head = [th.get_text(strip=True) for th in trs[0].find_all("th")]
    col = {name: head.index(name) for name in ("Age", "First", "Last", "City", "Loc")}
    out = []
    for tr in trs[1:]:
        cells = [td.get_text(" ", strip=True).replace("\xa0", " ").strip() for td in tr.find_all("td")]
        if len(cells) < len(head):
            continue
        age = cells[col["Age"]]  # e.g. "M30-39": gender + age group
        out.append({
            "year": year, "distance": dist, "did": did, "participant_id": "",
            "first": cells[col["First"]], "last": cells[col["Last"]],
            "city": cells[col["City"]], "state": cells[col["Loc"]].upper(),
            "age": age[1:] if age[:1] in "MFX" else age, "gender": age[:1] if age[:1] in "MFX" else "",
            "status": "registered", "place": "", "time": "",
        })
    return out


if __name__ == "__main__":
    main()
