# BURT 100 Runner Origins

Interactive map of where BURT 100 (Bainbridge Island, WA) entrants travel from, by year and
distance, built from UltraSignup results. Live page: https://burt-100.github.io/burt-origins/

The published page and this repo show counts by town only. Raw results (which include runner
names) are cached locally in `data/raw/` and are not checked in.

## Rebuild

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./pipeline/run_all.sh
```

A GitHub Action (`.github/workflows/refresh.yml`) re-pulls the upcoming edition's entrant lists
every Monday and republishes the page. It works only from the name-free files in `data/public/`,
and stops itself after race day, when a list comes back empty, or when it shrinks by more than half.
Run it on demand from the Actions tab, or:

```sh
gh workflow run refresh.yml
```

After race day, run the full pipeline locally to pull results (it needs `.burt_key`, the same
value as the `BURT_KEY_SECRET` repo secret, to hash runner names for the returning-runner count).

Before the race, always run the local pipeline with `--refresh` (and `git pull` first): without
it, the local entrant snapshot may be older than what the Action committed, and the rebuild would
roll the upcoming edition back.

To pull the latest entrant list yourself and republish:

```sh
./pipeline/run_all.sh --refresh
git add -A && git commit -m "Refresh entrants" && git push
```

Steps: discover dids → fetch results → parse → geocode (GeoNames, offline) → metrics → map.
Output: `docs/index.html` (GitHub Pages) and `site/burt-origins.html` (Claude artifact source).
Manual geocoding fixes live in `data/manual_geocode.csv`.
