#!/bin/sh
# Download the large reference datasets that aren't checked in (skips any already present).
# Usage: fetch_ref.sh [places]   (places = GeoNames only, all the weekly refresh needs)
set -e
REF="$(dirname "$0")/../data/ref"
mkdir -p "$REF"
if [ ! -f "$REF/us_places.tsv" ]; then
  # GeoNames US gazetteer, populated places only (feature class P).
  curl -sS -o "$REF/US.zip" https://download.geonames.org/export/dump/US.zip
  unzip -p "$REF/US.zip" US.txt | awk -F'\t' '$7=="P"' | cut -f1,2,3,5,6,8,11,12,15 > "$REF/us_places.tsv"
  rm "$REF/US.zip"
fi
if [ "$1" != "places" ] && [ ! -f "$REF/cb_county_500k.zip" ]; then
  curl -sS -o "$REF/cb_county_500k.zip" https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip
fi
