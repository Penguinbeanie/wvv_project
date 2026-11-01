#!/usr/bin/env python3
"""05_validity.py — attach validity windows to documents, trips and grid departures.

Reads:  data/fahrplaene_parsed/{documents,grid_departures,trips}.csv
Writes: same CSVs with an added valid_until column, plus document_validity.csv

Rule: a document is valid for a line from its valid_from until the valid_from
of the NEXT document (same line, later date) — open-ended ("") if none.
Documents with no line info (SEV / Baustellenfahrplan) are assumed to cover
every line present in the folder.

Usage: 05_validity.py [REPO_ROOT]
"""
import csv
import os
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
PARSED = os.path.join(REPO_ROOT, "data", "fahrplaene_parsed")


def read_csv(name):
    with open(os.path.join(PARSED, name), encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        return list(reader), fields


def write_csv(name, rows, fields):
    with open(os.path.join(PARSED, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    docs, doc_fields = read_csv("documents.csv")
    all_lines = sorted({ln for d in docs for ln in (d.get("lines") or "").split(",") if ln})

    # line -> sorted [(valid_from, pdf_name)]
    timeline = defaultdict(list)
    for d in docs:
        vf = d.get("valid_from") or ""
        if not vf:
            continue
        lines = [ln for ln in (d.get("lines") or "").split(",") if ln] or all_lines
        for ln in lines:
            timeline[ln].append((vf, d["pdf_name"]))

    # (pdf_name, line) -> valid_until
    until = {}
    for ln, entries in timeline.items():
        entries.sort()
        for i, (vf, pdf) in enumerate(entries):
            until[(pdf, ln)] = entries[i + 1][0] if i + 1 < len(entries) else ""

    # document-level fallback (rows with empty line): earliest per-line until
    doc_until = {}
    for d in docs:
        lns = [ln for ln in (d.get("lines") or "").split(",") if ln] or all_lines
        vals = [until.get((d["pdf_name"], ln), "") for ln in lns]
        vals = [v for v in vals if v]
        doc_until[d["pdf_name"]] = min(vals) if vals else ""

    def add_until(row):
        vf = row.get("valid_from") or ""
        row["valid_from"] = vf
        row["valid_until"] = until.get((row["pdf_name"], row.get("line") or ""),
                                       doc_until.get(row["pdf_name"], ""))
        return row

    for name in ("grid_departures.csv", "trips.csv"):
        rows, fields = read_csv(name)
        fields = fields + ["valid_until"] if "valid_until" not in fields else fields
        if "valid_from" not in fields:
            fields.append("valid_from")
        write_csv(name, [add_until(r) for r in rows], fields)

    val_rows = []
    for d in docs:
        vf = d.get("valid_from") or ""
        lns = [ln for ln in (d.get("lines") or "").split(",") if ln] or all_lines or [""]
        for ln in lns:
            val_rows.append({"pdf_name": d["pdf_name"], "line": ln, "valid_from": vf,
                             "valid_until": until.get((d["pdf_name"], ln), "")})
    write_csv("document_validity.csv", val_rows,
              ["pdf_name", "line", "valid_from", "valid_until"])
    print(f"validity: {len(val_rows)} document-line intervals written")


if __name__ == "__main__":
    main()
