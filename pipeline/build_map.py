"""Step 6: build site/burt-origins.html, a self-contained page (data + geometry inlined).

Public version: per-runner rows carry town, distance, status and miles only. No names
or UltraSignup ids are embedded.
"""
import csv
import json
from collections import defaultdict

from common import ROOT

DATA = ROOT / "data"
REF = DATA / "ref"
SITE = ROOT / "site"
DOCS = ROOT / "docs"
TEMPLATE = ROOT / "pipeline" / "map_template.html"

KEEP_COUNTRIES = {"124", "840", "484"}    # Canada, USA, Mexico


def prune_topology(topo, keep):
    """Keep only geometries for which keep(object_name, geom) is true; drop unused arcs."""
    objects = {}
    for name, obj in topo["objects"].items():
        geoms = [g for g in obj["geometries"] if keep(name, g)]
        objects[name] = {"type": "GeometryCollection", "geometries": geoms}
    used = set()

    def walk(a):
        if isinstance(a, int):
            used.add(a if a >= 0 else ~a)
        else:
            for x in a:
                walk(x)
    for obj in objects.values():
        for g in obj["geometries"]:
            walk(g.get("arcs", []))
    remap = {old: new for new, old in enumerate(sorted(used))}

    def rewrite(a):
        if isinstance(a, int):
            return remap[a] if a >= 0 else ~remap[~a]
        return [rewrite(x) for x in a]
    for obj in objects.values():
        for g in obj["geometries"]:
            g["arcs"] = rewrite(g.get("arcs", []))
    return {"type": "Topology", "transform": topo["transform"], "objects": objects,
            "arcs": [topo["arcs"][i] for i in sorted(used)]}


def main():
    rows = list(csv.DictReader(open(DATA / "runners_geo.csv")))
    runners = [{
        "y": int(r["year"]), "d": r["distance"],
        "town": r["geo_city"], "st": r["geo_state"],
        "lat": float(r["lat"]), "lon": float(r["lon"]),
        "region": r["region"], "mi": float(r["miles"]), "status": r["status"],
    } for r in rows]

    years = defaultdict(set)
    region_of = {}
    for r in rows:
        key = r["participant_id"] or f"{r['first']} {r['last']}".lower()
        years[key].add(r["year"])
        region_of[key] = r["region"]
    repeat_by_region = defaultdict(int)
    for k, v in years.items():
        if len(v) > 1:
            repeat_by_region[region_of[k]] += 1
    repeats = {"unique": len(years), "repeat": sum(repeat_by_region.values()),
               "byRegion": dict(repeat_by_region)}

    us = json.load(open(REF / "counties-10m.json"))
    # States only; WA comes from the detailed wa_counties.json instead.
    us = prune_topology(us, lambda n, g: n == "states" and g["id"] != "53")
    us["objects"].pop("nation", None)
    us["objects"].pop("counties", None)
    world = json.load(open(REF / "countries-50m.json"))
    world = prune_topology(world, lambda n, g: n == "countries" and g.get("id") in KEEP_COUNTRIES)
    world["objects"].pop("land", None)

    payload = {"runners": runners, "repeats": repeats, "us": us, "world": world,
               "wa": json.load(open(REF / "wa_counties.json"))}
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":")))
    # site/: artifact source (the artifact host adds the document skeleton on publish).
    SITE.mkdir(exist_ok=True)
    out = SITE / "burt-origins.html"
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")

    # docs/: standalone page for GitHub Pages, with its own skeleton.
    head, sep, body = html.partition("</style>")
    standalone = ('<!doctype html>\n<html lang="en">\n<head>\n'
                  '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                  + head + sep
                  + "\n</head>\n<body>\n" + body.lstrip("\n") + "\n</body>\n</html>\n")
    DOCS.mkdir(exist_ok=True)
    page = DOCS / "index.html"
    page.write_text(standalone)
    print(f"wrote {page} ({page.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
