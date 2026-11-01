#!/usr/bin/env bash
# 04_load_clickhouse.sh — apply schema, truncate, and load parsed CSVs into ClickHouse.
# Reads credentials from <repo>/clickhouse/.env. Idempotent: tables are truncated first.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CH_URL="${CLICKHOUSE_URL:-http://localhost:8123}"

USER_NAME="$(grep '^CLICKHOUSE_USER=' "$REPO_ROOT/clickhouse/.env" | cut -d= -f2-)"
PASSWORD="$(grep '^CLICKHOUSE_PASSWORD=' "$REPO_ROOT/clickhouse/.env" | cut -d= -f2-)"
AUTH=(-u "$USER_NAME:$PASSWORD")

q() { curl -sf --max-time 30 "$CH_URL/" "${AUTH[@]}" --data-binary "$1" || { echo "QUERY FAILED: $1" >&2; exit 1; }; }

# fresh reload each run (schema evolves; CSVs are regenerated)
for t in fahrplaene_documents fahrplaene_raw_pages fahrplaene_departures fahrplaene_footnotes fahrplaene_grid_departures fahrplaene_trips fahrplaene_document_validity fahrplaene_routes; do
  q "DROP TABLE IF EXISTS wvv.$t"
done

echo "applying schema..."
# ClickHouse HTTP rejects multi-statement bodies: strip comments, then send each statement separately
while IFS= read -r -d ';' stmt; do
  stmt="$(echo "$stmt" | tr -s ' \n' ' ')"
  [ -n "$stmt" ] && q "$stmt"
done < <(sed 's/--.*$//' "$SCRIPT_DIR/03_schema.sql")

PARSED="$REPO_ROOT/data/fahrplaene_parsed"
load() { # load <csv> <table>
  local query="INSERT INTO wvv.$2 FORMAT CSVWithNames"
  curl -sf --max-time 120 \
    "$CH_URL/?input_format_null_as_default=1&query=${query// /%20}" "${AUTH[@]}" \
    --data-binary @"$PARSED/$1" || { echo "LOAD FAILED: $1 -> wvv.$2" >&2; exit 1; }
  echo "loaded $1 -> wvv.$2"
}

load documents.csv        fahrplaene_documents
load raw_pages.csv        fahrplaene_raw_pages
load departures.csv       fahrplaene_departures
load footnotes.csv        fahrplaene_footnotes
load grid_departures.csv  fahrplaene_grid_departures
load trips.csv            fahrplaene_trips
load document_validity.csv fahrplaene_document_validity
load routes.csv           fahrplaene_routes

echo "row counts:"
q "SELECT 'documents', count() FROM wvv.fahrplaene_documents
   UNION ALL SELECT 'raw_pages', count() FROM wvv.fahrplaene_raw_pages
   UNION ALL SELECT 'departures', count() FROM wvv.fahrplaene_departures
   UNION ALL SELECT 'footnotes', count() FROM wvv.fahrplaene_footnotes
   UNION ALL SELECT 'grid_departures', count() FROM wvv.fahrplaene_grid_departures
   UNION ALL SELECT '  of which estimated', sum(estimated) FROM wvv.fahrplaene_grid_departures
   UNION ALL SELECT 'trips', count() FROM wvv.fahrplaene_trips
   UNION ALL SELECT 'document_validity', count() FROM wvv.fahrplaene_document_validity
   UNION ALL SELECT 'routes', count() FROM wvv.fahrplaene_routes FORMAT TSV"
