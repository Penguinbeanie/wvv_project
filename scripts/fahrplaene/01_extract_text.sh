#!/usr/bin/env bash
# 01_extract_text.sh — extract layout-preserving text from all PDFs in a Fahrplan folder.
# Usage: 01_extract_text.sh [PDF_DIR]
# Default PDF_DIR: the 1-2-3-4-5 folder on the Windows mount.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PDF_DIR="${1:-/mnt/c/Users/spaie/Downloads/Fahrplaene/Fahrplaene/1-2-3-4-5}"
OUT_DIR="$REPO_ROOT/data/fahrplaene_text"

mkdir -p "$OUT_DIR"

count=0
for pdf in "$PDF_DIR"/*.pdf; do
  [ -e "$pdf" ] || { echo "no PDFs found in $PDF_DIR" >&2; exit 1; }
  base="$(basename "$pdf" .pdf)"
  pdftotext -layout "$pdf" "$OUT_DIR/$base.txt"
  echo "extracted: $base.txt"
  count=$((count + 1))
done
echo "done: $count PDF(s) -> $OUT_DIR"
