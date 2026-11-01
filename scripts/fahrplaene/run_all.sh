#!/usr/bin/env bash
# run_all.sh — full repeatable pipeline for the Fahrplaene 1-2-3-4-5 test run:
#   PDFs -> layout text -> parsed CSVs -> ClickHouse tables.
# Usage: run_all.sh [PDF_DIR]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PDF_DIR="${1:-/mnt/c/Users/spaie/Downloads/Fahrplaene/Fahrplaene/1-2-3-4-5}"

bash "$SCRIPT_DIR/01_extract_text.sh" "$PDF_DIR"

VENV_PY="/home/Kai/projects/.venv/bin/python"
if [ -x "$VENV_PY" ]; then
  PY="$VENV_PY"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  PY=""  # fall back to docker below
fi

if [ -n "$PY" ]; then
  "$PY" "$SCRIPT_DIR/02_parse_timetables.py" "$REPO_ROOT"
  "$PY" "$SCRIPT_DIR/02b_parse_grids.py" "$REPO_ROOT" "$PDF_DIR"
  "$PY" "$SCRIPT_DIR/05_validity.py" "$REPO_ROOT"
  "$PY" "$SCRIPT_DIR/06_routes.py" "$REPO_ROOT"
else
  # no host python: run the parsers in a throwaway container
  docker run --rm -v "$REPO_ROOT":/work -v "$PDF_DIR":/pdfs:ro python:3.13-slim \
    sh -c "pip install -q pymupdf && python /work/scripts/fahrplaene/02_parse_timetables.py /work && python /work/scripts/fahrplaene/02b_parse_grids.py /work /pdfs && python /work/scripts/fahrplaene/05_validity.py /work && python /work/scripts/fahrplaene/06_routes.py /work"
fi

bash "$SCRIPT_DIR/04_load_clickhouse.sh"
