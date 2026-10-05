"""Step 1: discover every (year, distance) -> did for BURT 100. Writes dids.json.

Starts from a known did, reads the year links and distance tabs on each
results page, and crawls until no new dids appear.
"""
import json
import re

from common import BASE, ROOT, cached_get

SEED_DIDS = [130776, 120306, 110887, 110889]

YEAR_LINK = re.compile(r"<a href='/results_event\.aspx\?did=(\d+)'\s*>\s*(\d{4})\s*</a>")
DIST_LINK = re.compile(
    r"<a href='/results_event\.aspx\?did=(\d+)' class='event_(?:selected_)?link'\s*>([^<]+)</a>")
TITLE = re.compile(r"<title>\s*(\d{4})\s+(.+?)\s*-\s*Results", re.S)


def normalize_distance(label: str) -> str:
    s = label.strip().lower()
    if "100" in s and "mi" in s:
        return "100M"
    m = re.match(r"(\d+)\s*k", s)
    if m:
        return f"{m.group(1)}K"
    return label.strip()


def page(did: int) -> str:
    return cached_get(f"{BASE}/results_event.aspx?did={did}", f"results_page_{did}.html")


def main():
    seen, queue, out = set(), list(SEED_DIDS), {}
    while queue:
        did = queue.pop(0)
        if did in seen:
            continue
        seen.add(did)
        html = page(did)
        t = TITLE.search(html)
        year = int(t.group(1)) if t else None
        for d, label in DIST_LINK.findall(html):
            d = int(d)
            if year:
                out.setdefault(str(year), {})[normalize_distance(label)] = d
            queue.append(d)
        for d, _y in YEAR_LINK.findall(html):
            queue.append(int(d))
        if t:
            print(f"did {did}: {year} {t.group(2).strip()}")

    out = {y: dict(sorted(v.items())) for y, v in sorted(out.items())}
    (ROOT / "dids.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
