#!/usr/bin/env python3
"""
Pull BURT 100 results + entrant lists from UltraSignup (undocumented endpoints).
Usage:  pip install requests
        python burt_pull.py
Output: ./burt_data/  -> zip it and upload to Claude.

Fill in DIDS: open each year's results page on UltraSignup, switch between the
55K / 110K / 100M tabs, and copy the did=NNNNN from the URL for each.
"""
import json, time, pathlib, requests

DIDS = {
    # (year, distance): did
    (2026, "55K"): None, (2026, "110K"): None, (2026, "100M"): None,
    (2025, "55K"): None, (2025, "110K"): None, (2025, "100M"): None,
    (2024, "55K"): None, (2024, "110K"): None, (2024, "100M"): None,
    (2023, "55K"): None, (2023, "110K"): None, (2023, "100M"): None,
    (2022, "55K"): None, (2022, "110K"): None, (2022, "100M"): None,
}

H = {"User-Agent": "Mozilla/5.0 (personal BURT analysis)"}
OUT = pathlib.Path("burt_data"); OUT.mkdir(exist_ok=True)

for (year, dist), did in DIDS.items():
    if not did:
        continue
    tag = f"{year}_{dist}_{did}"
    try:
        r = requests.get(f"https://ultrasignup.com/service/events.svc/results/{did}/json?_search=false",
                         headers=H, timeout=20)
        (OUT / f"results_{tag}.json").write_text(r.text)
        n = len(r.json()) if r.ok else "ERR"
    except Exception as e:
        n = f"ERR {e}"
    # Entrant list page (includes registrants who never started, if still shown)
    try:
        e = requests.get(f"https://ultrasignup.com/entrants_event.aspx?did={did}", headers=H, timeout=20)
        (OUT / f"entrants_{tag}.html").write_text(e.text)
    except Exception as ex:
        print("entrants failed", tag, ex)
    print(f"{tag}: {n} result rows")
    time.sleep(2)  # be polite

print("Done ->", OUT.resolve())
