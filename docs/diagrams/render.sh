#!/usr/bin/env bash
# Render all Graphviz diagrams to SVG + PNG.
# Requires: sudo apt install graphviz
set -euo pipefail
cd "$(dirname "$0")"

for f in *.dot; do
    base="${f%.dot}"
    dot -Tsvg "$f" -o "$base.svg"
    dot -Tpng -Gdpi=200 "$f" -o "$base.png"
    echo "rendered $base.svg + $base.png"
done
