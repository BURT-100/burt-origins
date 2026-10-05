"""Step 2: fetch results JSON + entrants HTML for every did in dids.json, and dated
entrant-list snapshots for the upcoming edition in upcoming.json (if any).

Usage: python fetch.py [--refresh]   (--refresh takes a new snapshot of open entrant lists)
"""
import json
import sys

from common import BASE, ROOT, cached_get, snapshot_get


def main():
    refresh = "--refresh" in sys.argv
    dids = json.loads((ROOT / "dids.json").read_text())
    for year, by_dist in dids.items():
        for dist, did in by_dist.items():
            print(f"{year} {dist} ({did})")
            cached_get(f"{BASE}/service/events.svc/results/{did}/1/json?_search=false&rows=10000&page=1",
                       f"results_{did}.json")
            cached_get(f"{BASE}/entrants_event.aspx?did={did}", f"entrants_{did}.html")

    up = ROOT / "upcoming.json"
    if up.exists():
        upcoming = json.loads(up.read_text())
        for dist, did in upcoming["dids"].items():
            # No results exist yet, so never request (and permanently cache) the results JSON.
            _, date = snapshot_get(f"{BASE}/entrants_event.aspx?did={did}", f"entrants_{did}", refresh)
            print(f"{upcoming['year']} {dist} ({did}) entrants snapshot {date}")


if __name__ == "__main__":
    main()
