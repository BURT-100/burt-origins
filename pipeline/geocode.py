"""Step 4: geocode city/state offline against GeoNames US populated places.

Inputs:  data/runners.csv, data/ref/us_places.tsv (GeoNames US, feature class P),
         data/manual_geocode.csv (overrides: raw city/state -> fixed city/state or lat/lon)
Outputs: data/runners_geo.csv, data/unmatched.csv (rows needing a manual fix; never dropped)
"""
import csv
import math
import re

from common import ROOT

DATA = ROOT / "data"
# Battle Point Park, Bainbridge Island, WA (start/finish)
RACE_LAT, RACE_LON = 47.6683, -122.5463

KITSAP = ("WA", "035")
KING = ("WA", "033")


def norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[.,']", "", s)
    s = re.sub(r"^(st|ste)\s", "saint ", s)
    s = re.sub(r"^mt\s", "mount ", s)
    s = re.sub(r"^ft\s", "fort ", s)
    return re.sub(r"\s+", " ", s)


def miles(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_places():
    """(norm name, state) -> best place (city-type PPL with highest population wins)."""
    rank = {"PPLA": 0, "PPLA2": 1, "PPL": 2, "PPLA3": 3, "PPLL": 5, "PPLX": 6}
    best = {}
    with open(DATA / "ref" / "us_places.tsv") as f:
        for line in f:
            gid, name, ascii_, lat, lon, fcode, st, county, pop = line.rstrip("\n").split("\t")
            pop = int(pop or 0)
            cand = (lat, lon, county, name, rank.get(fcode, 4), pop)
            for key in {(norm(name), st), (norm(ascii_), st)}:
                cur = best.get(key)
                if cur is None or (-pop, cand[4]) < (-cur[5], cur[4]):
                    best[key] = cand
    return best


def load_overrides():
    out = {}
    path = DATA / "manual_geocode.csv"
    if path.exists():
        with open(path) as f:
            for r in csv.DictReader(f):
                out[(norm(r["raw_city"]), r["raw_state"].upper())] = r
    return out


def main():
    places, overrides = load_places(), load_overrides()
    rows, unmatched = [], []
    with open(DATA / "runners.csv") as f:
        for r in csv.DictReader(f):
            city, st = r["city"], r["state"]
            ov = overrides.get((norm(city), st))
            lat = lon = county = None
            geo_city, geo_state, how = city, st, "gazetteer"
            if ov:
                geo_city, geo_state = ov["city"] or city, ov["state"] or st
                how = "manual"
                if ov.get("lat") and ov.get("lon"):
                    lat, lon, county = float(ov["lat"]), float(ov["lon"]), ov.get("county_fips", "")
            if lat is None:
                hit = places.get((norm(geo_city), geo_state))
                if hit:
                    lat, lon, county = float(hit[0]), float(hit[1]), hit[2]
                    geo_city = hit[3]
            if lat is None:
                unmatched.append(r)
                r.update(geo_city="", geo_state="", lat="", lon="", county_fips="", region="unknown",
                         miles="", geo_source="unmatched")
            else:
                r.update(geo_city=geo_city, geo_state=geo_state, lat=round(lat, 5), lon=round(lon, 5),
                         county_fips=county, region=region(geo_city, geo_state, county),
                         miles=round(miles(RACE_LAT, RACE_LON, lat, lon), 1), geo_source=how)
            rows.append(r)

    with open(DATA / "runners_geo.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(DATA / "unmatched.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["year", "distance", "city", "state"], extrasaction="ignore")
        w.writeheader()
        w.writerows(unmatched)
    print(f"geocoded {len(rows) - len(unmatched)}/{len(rows)}; unmatched -> data/unmatched.csv")
    for r in unmatched:
        print(f"  UNMATCHED {r['year']} {r['distance']}: {r['city']!r}, {r['state']!r}")


def region(city, state, county):
    if state == "WA" and norm(city) == "bainbridge island":
        return "Bainbridge Island"
    if (state, county) == KITSAP:
        return "Kitsap County"
    if (state, county) == KING:
        return "King County"
    if state == "WA":
        return "Other WA"
    return "Out of state"


if __name__ == "__main__":
    main()
