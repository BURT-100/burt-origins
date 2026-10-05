#!/bin/sh
# Rebuild everything. Finished races are fetched once and cached in data/raw.
# Pass --refresh to take a new snapshot of the upcoming edition's entrant list.
set -e
cd "$(dirname "$0")"
PY=../.venv/bin/python
./fetch_ref.sh
$PY discover.py "$@"
$PY fetch.py "$@"
$PY parse.py
$PY geocode.py
$PY metrics.py
$PY wa_shapes.py
$PY build_map.py
