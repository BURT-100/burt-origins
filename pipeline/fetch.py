"""Step 2: fetch results JSON + entrants HTML for every did in dids.json."""
import json

from common import BASE, ROOT, cached_get


def main():
    dids = json.loads((ROOT / "dids.json").read_text())
    for year, by_dist in dids.items():
        for dist, did in by_dist.items():
            print(f"{year} {dist} ({did})")
            cached_get(f"{BASE}/service/events.svc/results/{did}/1/json?_search=false&rows=10000&page=1",
                       f"results_{did}.json")
            cached_get(f"{BASE}/entrants_event.aspx?did={did}", f"entrants_{did}.html")


if __name__ == "__main__":
    main()
