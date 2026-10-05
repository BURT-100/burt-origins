"""Name-free data that is safe to commit, shared by the local pipeline and the weekly refresh.

data/public/runners.csv  one row per mapped entrant: year, distance, status, town, region, miles.
data/public/repeats.json repeat-runner summary across completed editions.
data/public/past_keys.txt keyed hashes (HMAC-SHA256) of completed-edition runner names, one per
                         line and not linked to any row. They let the refresh count returning
                         registrants without names in the repo. The key lives in BURT_KEY_SECRET
                         (GitHub Actions secret) or the gitignored .burt_key file locally.
"""
import csv
import hashlib
import hmac
import json
import os

from common import ROOT

PUBLIC = ROOT / "data" / "public"
FIELDS = ["year", "distance", "status", "geo_city", "geo_state", "lat", "lon", "region", "miles"]


def runner_key(r) -> str:
    """Normalized name; entrant lists carry no UltraSignup id, so name is the key across years."""
    return " ".join(f"{r['first']} {r['last']}".lower().split())


def _secret() -> bytes:
    s = os.environ.get("BURT_KEY_SECRET")
    if not s and (ROOT / ".burt_key").exists():
        s = (ROOT / ".burt_key").read_text().strip()
    if not s:
        raise SystemExit("Set BURT_KEY_SECRET or create .burt_key (see pipeline/public.py)")
    return s.encode()


def hashed_keys(rows) -> set[str]:
    secret = _secret()
    return {hmac.new(secret, runner_key(r).encode(), hashlib.sha256).hexdigest()[:20] for r in rows}


def read_runners() -> list[dict]:
    with open(PUBLIC / "runners.csv") as f:
        return list(csv.DictReader(f))


def write_runners(rows):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (int(r["year"]), r["distance"], r["status"], r["geo_city"]))
    with open(PUBLIC / "runners.csv", "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def read_past_keys() -> set[str]:
    return set((PUBLIC / "past_keys.txt").read_text().split())


def write_past_keys(keys):
    (PUBLIC / "past_keys.txt").write_text("".join(f"{k}\n" for k in sorted(keys)))


def load_upcoming():
    path = ROOT / "upcoming.json"
    return json.loads(path.read_text()) if path.exists() else None


def save_upcoming(up):
    (ROOT / "upcoming.json").write_text(json.dumps(up, indent=2) + "\n")
