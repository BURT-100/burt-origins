"""Shared helpers: polite cached HTTP fetches against UltraSignup."""
import pathlib
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://ultrasignup.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal BURT 100 origin analysis)"}
SLEEP_S = 2.5

_last_request = 0.0


def cached_get(url: str, cache_name: str) -> str:
    """Return the body of `url`, reading from data/raw/<cache_name> if present.

    Never re-fetches cached data. Sleeps between live requests.
    """
    global _last_request
    path = RAW / cache_name
    if path.exists():
        return path.read_text()
    wait = SLEEP_S - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    r = requests.get(url, headers=HEADERS, timeout=30)
    _last_request = time.time()
    r.raise_for_status()
    path.write_text(r.text)
    print(f"  fetched {url} -> {path.name}")
    return r.text


def snapshot_get(url: str, prefix: str, refresh: bool) -> tuple[str, str]:
    """Fetch a page that changes over time (an open entrant list) as a dated snapshot.

    Saves data/raw/<prefix>_<YYYY-MM-DD>.html. Without `refresh`, reuses the newest
    existing snapshot and only fetches if there is none. Returns (body, snapshot date).
    """
    existing = latest_snapshot(prefix)
    today = time.strftime("%Y-%m-%d")
    if existing and (not refresh or existing[1] == today):
        return existing[0].read_text(), existing[1]
    return cached_get(url, f"{prefix}_{today}.html"), today


def latest_snapshot(prefix: str):
    """(path, date) of the newest data/raw/<prefix>_<date>.html, or None."""
    snaps = sorted(RAW.glob(f"{prefix}_????-??-??.html"))
    if not snaps:
        return None
    return snaps[-1], snaps[-1].stem.rsplit("_", 1)[1]
