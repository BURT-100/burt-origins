#!/bin/sh
# Rebuild everything. Network fetches are cached in data/raw and never repeated.
set -e
cd "$(dirname "$0")"
PY=../.venv/bin/python
./fetch_ref.sh
$PY discover.py
$PY fetch.py
$PY parse.py
$PY geocode.py
$PY metrics.py
$PY wa_shapes.py
$PY build_map.py
