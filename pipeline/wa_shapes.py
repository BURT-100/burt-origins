"""Extract WA county polygons from Census cb_2023_us_county_500k into data/ref/wa_counties.json.

The 1:10M us-atlas shoreline is too coarse for Puget Sound (Bainbridge disappears), so the
local view uses these 1:500k shapes, lightly simplified.
"""
import io
import json
import zipfile

import shapefile

from common import ROOT

REF = ROOT / "data" / "ref"
TOL = 0.0012  # degrees (~100 m), Douglas-Peucker tolerance


def rdp(pts, tol):
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        norm = (dx * dx + dy * dy) ** 0.5 or 1e-12
        best, idx = 0.0, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / norm
            if d > best:
                best, idx = d, i
        if best > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def main():
    z = zipfile.ZipFile(REF / "cb_county_500k.zip")
    base = "cb_2023_us_county_500k"
    sf = shapefile.Reader(shp=io.BytesIO(z.read(f"{base}.shp")), dbf=io.BytesIO(z.read(f"{base}.dbf")),
                          shx=io.BytesIO(z.read(f"{base}.shx")))
    fields = [f[0] for f in sf.fields[1:]]
    feats = []
    for sr in sf.iterShapeRecords():
        rec = dict(zip(fields, sr.record))
        if rec["STATEFP"] != "53":
            continue
        shp = sr.shape
        parts = list(shp.parts) + [len(shp.points)]
        rings = []
        for a, b in zip(parts, parts[1:]):
            pts = [(round(x, 4), round(y, 4)) for x, y in shp.points[a:b]]
            # A closed ring's endpoints coincide, so simplify it as two open halves.
            mid = len(pts) // 2
            ring = rdp(pts[:mid + 1], TOL)[:-1] + rdp(pts[mid:], TOL)
            # Shapefile exteriors are clockwise, which is what d3 expects. Counter-clockwise
            # rings are holes; drop them, since a lone CCW ring would render as the whole globe.
            signed = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:]))
            if len(ring) >= 4 and signed < 0:
                rings.append([list(p) for p in ring])
        feats.append({"type": "Feature", "properties": {"name": rec["NAME"], "fips": rec["COUNTYFP"]},
                      "geometry": {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}})
    out = {"type": "FeatureCollection", "features": feats}
    (REF / "wa_counties.json").write_text(json.dumps(out, separators=(",", ":")))
    print(f"{len(feats)} WA counties, {(REF / 'wa_counties.json').stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
