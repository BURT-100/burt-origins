"""Step 1: discover every (year, distance) -> did for BURT 100. Writes dids.json.

Starts from a known did, reads the year links and distance tabs on each
results page, and crawls until no new dids appear. Then checks the event's
registration page for an upcoming edition that has no results yet and writes
upcoming.json (year, race date, dids, caps), or removes it if there is none.

Usage: python discover.py [--refresh]   (--refresh re-reads the live event page)
"""
import json
import re
import sys
import time

from common import BASE, ROOT, cached_get, snapshot_get

SEED_DIDS = [130776, 120306, 110887, 110889]

YEAR_LINK = re.compile(r"<a href='/results_event\.aspx\?did=(\d+)'\s*>\s*(\d{4})\s*</a>")
DIST_LINK = re.compile(
    r"<a href='/results_event\.aspx\?did=(\d+)' class='event_(?:selected_)?link'\s*>([^<]+)</a>")
TITLE = re.compile(r"<title>\s*(\d{4})\s+(.+?)\s*-\s*Results", re.S)


def normalize_distance(label: str) -> str:
    s = label.strip().lower()
    if re.match(r"100\s*(mi|m\b|m$)", s):
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

    latest = out[max(out)]
    upcoming = find_upcoming(page(next(iter(latest.values()))), set(out), "--refresh" in sys.argv)
    path = ROOT / "upcoming.json"
    if upcoming:
        path.write_text(json.dumps(upcoming, indent=2) + "\n")
        print("upcoming:", json.dumps(upcoming))
    elif path.exists():
        path.unlink()
        print("no upcoming edition; removed upcoming.json")


def find_upcoming(results_html: str, result_years: set, refresh: bool):
    """Follow results page -> registration page -> event page to the current edition."""
    dtid = re.search(r"register\.aspx\?dtid=(\d+)", results_html).group(1)
    reg = cached_get(f"{BASE}/register.aspx?dtid={dtid}", f"register_dtid_{dtid}.html")
    eid = re.search(r"register\.aspx\?eid=(\d+)", reg).group(1)
    # The eid page always shows the event's current edition, so it is a dated snapshot.
    event, _ = snapshot_get(f"{BASE}/register.aspx?eid={eid}", f"register_eid_{eid}", refresh)
    t = re.search(r"<title>\s*[^<]*?-\s*([A-Z][a-z]+ \d{1,2}, (\d{4}))", event)
    if not t or t.group(2) in result_years:
        return None
    year, race_date = t.group(2), time.strftime("%Y-%m-%d", time.strptime(t.group(1), "%B %d, %Y"))
    did = re.search(r"entrants_event\.aspx\?did=(\d+)", event).group(1)
    entrants, _ = snapshot_get(f"{BASE}/entrants_event.aspx?did={did}", f"entrants_{did}", refresh)
    dids = {}
    for d, label in re.findall(r"<a[^>]+entrants_event\.aspx\?did=(\d+)[^>]*>([^<]{1,40})</a>", entrants):
        dist = normalize_distance(label)
        if dist in ("55K", "110K", "100M"):
            dids[dist] = int(d)
    text = re.sub(r"<[^>]+>", " ", event)
    caps = {normalize_distance(f"{n} {u}"): int(c) for n, u, c in
            re.findall(r"(\d+)\s*(k|M)\w*\s*:\s*(\d+)\s*runners", text)}
    return {"year": int(year), "race_date": race_date, "eid": int(eid),
            "dids": dict(sorted(dids.items())), "caps": caps}


if __name__ == "__main__":
    main()
