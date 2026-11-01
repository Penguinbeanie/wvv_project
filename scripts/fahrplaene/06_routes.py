#!/usr/bin/env python3
"""06_routes.py — build the routes dimension table from parsed grid departures.

Reads:  data/fahrplaene_parsed/{grid_departures,document_validity}.csv
Writes: data/fahrplaene_parsed/routes.csv

One row per (line, direction): start/end stop taken from the min/max stop_seq
of its trips, plus trip/document counts and the validity span seen so far.
Use this table to cross-reference line+direction when a newly parsed document
is missing its header (match on line + direction or on start/end stops).

Usage: 06_routes.py [REPO_ROOT]
"""
import csv
import os
import re
import sys
from collections import defaultdict


def norm_direction(d):
    """Normalize dash variants so 'Sanderau - Zellerau' and 'Sanderau – Zellerau'
    land on the same route row."""
    return re.sub(r"\s*[–—]\s*", " - ", d).strip(" -")

REPO_ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
PARSED = os.path.join(REPO_ROOT, "data", "fahrplaene_parsed")


def main():
    with open(os.path.join(PARSED, "grid_departures.csv"), encoding="utf-8") as fh:
        deps = list(csv.DictReader(fh))

    # (line, direction) -> trip -> (min_seq, start, max_seq, end), plus pdf set
    routes = defaultdict(lambda: {"trips": {}, "pdfs": set(), "vf": [], "vu": []})
    for d in deps:
        if d["estimated"] == "1" or not d["line"] or not d["direction"]:
            continue
        key = (d["line"], norm_direction(d["direction"]))
        r = routes[key]
        r["pdfs"].add(d["pdf_name"])
        if d.get("valid_from"):
            r["vf"].append(d["valid_from"])
        if d.get("valid_until"):
            r["vu"].append(d["valid_until"])
        seq = int(d["stop_seq"])
        t = r["trips"].setdefault(d["trip_id"], [seq, d["stop"], seq, d["stop"]])
        if seq < t[0]:
            t[0], t[1] = seq, d["stop"]
        if seq > t[2]:
            t[2], t[3] = seq, d["stop"]

    rows = []
    for (line, direction), r in sorted(routes.items()):
        starts = [t[1] for t in r["trips"].values()]
        ends = [t[3] for t in r["trips"].values()]
        rows.append({
            "line": line, "direction": direction,
            "start_stop": max(set(starts), key=starts.count),
            "end_stop": max(set(ends), key=ends.count),
            "n_trips": len(r["trips"]), "n_documents": len(r["pdfs"]),
            "first_valid_from": min(r["vf"]) if r["vf"] else "",
            "last_valid_until": max(r["vu"]) if r["vu"] else "",
        })

    # QA: routes whose start/end "stops" are actually times or placeholders are junk
    bad = [r for r in rows if re.search(r"\d{1,2}:\d{2}", r["start_stop"] + r["end_stop"])
           or "(row" in r["start_stop"] + r["end_stop"]]
    for r in bad:
        print(f"  WARNING: dropped junk route line={r['line']} -> {r['direction']!r}: "
              f"start={r['start_stop']!r} end={r['end_stop']!r}", file=sys.stderr)
    rows = [r for r in rows if r not in bad]

    # merge directions that share the same end stop (spelling variants like
    # "Grombühl" vs "Grombühl/Unikliniken"); "ab"/"an" markers are ignored
    def end_key(stop):
        return re.sub(r"\s*(ab|an)$", "", stop).strip().lower()

    by_end = defaultdict(list)
    for r in rows:
        by_end[(r["line"], end_key(r["end_stop"]))].append(r)
    merged = []
    for (line, _), group in sorted(by_end.items()):
        canon = max(group, key=lambda r: r["n_trips"])
        merged.append({**canon,
                       "n_trips": sum(r["n_trips"] for r in group),
                       "n_documents": max(r["n_documents"] for r in group)})
    rows = sorted(merged, key=lambda r: (r["line"], r["direction"]))

    with open(os.path.join(PARSED, "routes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["line", "direction", "start_stop", "end_stop",
                                           "n_trips", "n_documents", "first_valid_from",
                                           "last_valid_until"])
        w.writeheader()
        w.writerows(rows)
    print(f"routes: {len(rows)} line/direction combinations")
    # short enough to eyeball every run — please review
    print(f"{'line':>4}  {'direction':<26}  {'start_stop':<34}  {'end_stop':<34}  {'trips':>5}  docs")
    for r in rows:
        print(f"{r['line']:>4}  {r['direction']:<26}  {r['start_stop']:<34}  "
              f"{r['end_stop']:<34}  {r['n_trips']:>5}  {r['n_documents']}")


if __name__ == "__main__":
    main()
