# BURT 100 Runner Origins

Interactive map of where BURT 100 (Bainbridge Island, WA) entrants travel from, by year and
distance, built from UltraSignup results. Live page: https://gosborn.github.io/burt-origins/

The published page and this repo show counts by town only. Raw results (which include runner
names) are cached locally in `data/raw/` and are not checked in.

## Rebuild

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./pipeline/run_all.sh
```

To pull the latest entrant list for the upcoming edition (currently 2027) and republish:

```sh
./pipeline/run_all.sh --refresh
git add -A && git commit -m "Refresh entrants" && git push
```

Steps: discover dids → fetch results → parse → geocode (GeoNames, offline) → metrics → map.
Output: `docs/index.html` (GitHub Pages) and `site/burt-origins.html` (Claude artifact source).
Manual geocoding fixes live in `data/manual_geocode.csv`.
