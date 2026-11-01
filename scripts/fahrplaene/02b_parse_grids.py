#!/usr/bin/env python3
"""02b_parse_grids.py — coordinate-based timetable grid extraction with PyMuPDF.

Reads:  PDFs from the Fahrplaene folder (default: .../Fahrplaene/1-2-3-4-5)
Writes: <repo>/data/fahrplaene_parsed/grid_departures.csv
        <repo>/data/fahrplaene_parsed/trips.csv

Usage: 02b_parse_grids.py [REPO_ROOT] [PDF_DIR]

Model:
  - a page with >= 8 "HH:MM" words is a timetable grid page
  - time words are clustered by x into trip COLUMNS and by y into stop ROWS
    -> every real cell links a stop to a trip: (page, column) = trip_id
  - stop names = words left of the first time column, merged across wrapped
    lines by assigning each text line to the nearest time row
  - non-time words inside the grid become cell notes ("usw.", "alle 15 min", "bis 12:00", "A", ...)
  - "usw." gaps are filled per stop row: cadence from "alle N min" if present,
    else the mode of consecutive time differences before the gap; times are
    generated between the last shown and first shown time (or up to a "bis"
    bound) and marked estimated=1 with a synthetic trip_id
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

import pymupdf

REPO_ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
PDF_DIR = sys.argv[2] if len(sys.argv) > 2 else "/mnt/c/Users/spaie/Downloads/Fahrplaene/Fahrplaene/1-2-3-4-5"
OUT_DIR = os.path.join(REPO_ROOT, "data", "fahrplaene_parsed")

TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
ANY_TIME_RE = re.compile(r"\d{1,2}:\d{2}")
DIRECTION_RE = re.compile(r"^\s*(\d{1,3})\s+(\S.*(?:-|–).*)$")
DAYTYPE_PATTERNS = [
    ("montags-freitags", "Mon-Fri"), ("montag-freitags", "Mon-Fri"),
    ("montags - freitags", "Mon-Fri"), ("werktag", "Mon-Fri"),
    ("samstag", "Sat"),
    ("sonn- und feiertag", "Sun-Hol"), ("sonn-/feiertag", "Sun-Hol"),
    ("feiertag", "Sun-Hol"), ("schultag", "School"),
]
ALLE_RE = re.compile(r"alle\s+(\d+)\s*min", re.I)
BIS_RE = re.compile(r"bis\s+(\d{1,2}:\d{2})", re.I)
MIN_GRID_TIMES = 8
COL_X_GAP = 10.0   # pt; time columns are ~23pt apart
ROW_Y_GAP = 5.0    # pt; stop rows are ~9pt apart


def t2m(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def m2t(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def cluster(values, gap):
    """Cluster sorted numeric values; return list of (center, [values])."""
    out = []
    for v in sorted(values):
        if out and v - out[-1][1][-1] <= gap:
            out[-1][1].append(v)
        else:
            out.append((v, [v]))
    return [(sum(g) / len(g), g) for _, g in out]


def page_lines_above(page, y_limit):
    """Structural text lines with y0 < y_limit; fragments on the same visual
    row (e.g. the line number '1' and its route text) are merged into one line."""
    items = []
    for block in page.get_text("dict")["blocks"]:
        for ln in block.get("lines", []):
            text = " ".join(s["text"] for s in ln["spans"]).strip()
            if text and ln["bbox"][1] < y_limit:
                items.append((ln["bbox"][1], ln["bbox"][0], text))
    items.sort()
    merged = []
    for y, x, text in items:
        if merged and abs(merged[-1][0] - y) <= 3:
            merged[-1][2] += " " + text
        else:
            merged.append([y, x, text])
    return [(y, t) for y, _, t in merged]


def detect_context(page, grid_top, doc_lines=()):
    """Closest day-type label and direction header above the grid.

    Direction headers print as a bare line number on one text line and the
    route ("Sanderau - Hauptbahnhof - ...") on another line a few pt away, so
    a number-only line is combined with a nearby route line. Bare numbers not
    in the document's known line numbers are rejected (page numbers etc.)."""
    lines = page_lines_above(page, grid_top - 4)  # bottom-most last
    line, direction, day = "", "", ""
    for i in range(len(lines) - 1, -1, -1):
        y, text = lines[i]
        low = text.lower()
        if not day:
            for pat, label in DAYTYPE_PATTERNS:
                if pat in low:
                    day = label
                    break
        if not line and not ANY_TIME_RE.search(text):
            m = re.search(r"\b(\d{1,3})(?:\s*/\s*\d{1,3})*\s*/\s*SEV\b", text, re.I)
            if m:  # replacement-service header, e.g. "5 / SEV" or "4 / 5 / SEV"
                line = m.group(1)
            else:
                m = re.search(r"\b(\d{1,3})\s+([A-ZÄÖÜ]\S*(?:\s[-–]\s*\S+)+)", text)
                if m:  # number and route on the same line
                    route = m.group(2).split(" Siehe ")[0]
                    line, direction = m.group(1), re.sub(r"\s+", " ", route).strip(" -–")
                elif re.fullmatch(r"\d{1,3}", text.strip()):  # bare number: find route nearby
                    num = text.strip()
                    if not doc_lines or num in doc_lines:  # reject page numbers etc.
                        for jy, jt in lines:
                            if abs(jy - y) <= 14 and re.search(r"\s[-–]\s", jt) and not ANY_TIME_RE.search(jt):
                                line = num
                                direction = re.sub(r"\s+", " ", jt.split(" Siehe ")[0]).strip(" -–")
                                break
                elif re.search(r"[A-Za-zÄÖÜäöü]", text):
                    # line number merged into a header line, e.g. "2 Würzburger Straßenbahn GmbH   1"
                    m2 = re.search(r"\b(\d{1,3})\s*$", text)
                    if m2 and (not doc_lines or m2.group(1) in doc_lines):
                        for jy, jt in lines:
                            if abs(jy - y) <= 14 and re.search(r"\s[-–]\s", jt) and not ANY_TIME_RE.search(jt):
                                line = m2.group(1)
                                direction = re.sub(r"\s+", " ", jt.split(" Siehe ")[0]).strip(" -–")
                                break
        if not direction and re.search(r"\s[-–]\s", text) and not ANY_TIME_RE.search(text) \
                and re.search(r"[A-Za-zÄÖÜäöü]{3}", text) \
                and not re.search(r"App|herunterladen|Echtzeit|kostenlos|VVM|umsteigen", text, re.I):
            # route without a line number (e.g. SEV headers): keep it as direction only
            direction = re.sub(r"\s+", " ", text.split(" Siehe ")[0]).strip(" -–")
        if line and day:
            break
    return line, direction, day


def doc_key(pdf_name):
    """Short unique slug per document, embedded in trip_id so ids are globally
    unique across all PDFs (e.g. linie_1_5_ab_14_09_2021_p3c02)."""
    stem = os.path.splitext(pdf_name)[0].lower()
    return re.sub(r"[^a-z0-9]+", "_", stem).strip("_")


def load_doc_validity(repo_root):
    """pdf_name -> (valid_from ISO, [line numbers]) from documents.csv (step 02)."""
    path = os.path.join(repo_root, "data", "fahrplaene_parsed", "documents.csv")
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                lines = [x for x in (row.get("lines") or "").split(",") if x]
                out[row["pdf_name"]] = (row.get("valid_from") or "", lines)
    return out


GRID_BLOCK_GAP = 25.0  # vertical gap (pt) that separates two grids on one page


def dest_of(route):
    """Normalize a full route string to its destination: the last token after the
    final spaced dash ("Zellerau - Stadtmitte - Hauptbahnhof - Sanderau" -> "Sanderau").
    Only ' - ' style separators are split, so compounds like "Uni-Kliniken" stay
    intact; a compound like "Grombühl/Unikliniken" is reduced to its main part
    so spelling variants collapse to one destination."""
    toks = [re.sub(r"[()]", "", t).strip() for t in re.split(r"\s+[-–—]\s+", route)]
    toks = [t for t in toks if t]
    dest = toks[-1] if toks else route.strip()
    return dest.split("/")[0].strip() if "/" in dest else dest


def parse_grid_page(pdf_name, pno, page, dk, valid_from, inherit=("", "", ""), doc_lines=()):
    """A page can hold several grids (e.g. forward + reverse direction): split the
    time rows into blocks wherever the vertical gap exceeds GRID_BLOCK_GAP and
    parse each block with its own context, columns and trip ids."""
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,word_no
    times = [w for w in words if TIME_RE.match(w[4])]
    if len(times) < MIN_GRID_TIMES:
        return None
    row_centers = sorted(c for c, _ in cluster([w[1] for w in times], ROW_Y_GAP))
    blocks = [[row_centers[0]]]
    for y in row_centers[1:]:
        if y - blocks[-1][-1] > GRID_BLOCK_GAP:
            blocks.append([y])
        else:
            blocks[-1].append(y)
    dep_all, trip_all = [], []
    ctx = list(inherit)
    for bi, brow in enumerate(blocks):
        btimes = [w for w in times if brow[0] - ROW_Y_GAP <= w[1] <= brow[-1] + ROW_Y_GAP]
        d, t, detected = parse_grid_block(pdf_name, pno, bi, page, words, btimes, brow,
                                          dk, valid_from, inherit=tuple(ctx), doc_lines=doc_lines)
        ctx = [detected[i] or ctx[i] for i in range(3)]
        dep_all += d
        trip_all += t
    return dep_all, trip_all, tuple(ctx)


def parse_grid_block(pdf_name, pno, bi, page, words, times, row_y, dk, valid_from,
                     inherit=("", "", ""), doc_lines=()):
    grid_top, grid_bottom = min(row_y) - 2, max(row_y) + 6
    cols = cluster([w[0] for w in times], COL_X_GAP)          # [(cx, [x...])]
    col_x = [c for c, _ in cols]
    first_col_x = min(col_x)

    def col_of(x):
        return min(range(len(col_x)), key=lambda i: abs(col_x[i] - x))

    def row_of(y):
        return min(range(len(row_y)), key=lambda i: abs(row_y[i] - y))

    # stop names: words left of the first time column, only within the grid's row
    # band (legend lines above the grid are excluded), merged into nearest row.
    # Time words and bare numbers never become stop names.
    left_lines = defaultdict(list)
    for w in words:
        if w[2] < first_col_x - 3 and grid_top - 10 <= w[1] <= grid_bottom + 4:
            if TIME_RE.match(w[4]) or re.fullmatch(r"\d{1,3}", w[4]):
                continue
            left_lines[round(w[1] / ROW_Y_GAP)].append(w)
    stop_by_row = defaultdict(list)
    for _, ws in sorted(left_lines.items()):
        ws.sort(key=lambda w: w[0])
        y = min(w[1] for w in ws)
        r = row_of(y)
        if abs(row_y[r] - y) <= 8:  # drop text lines that don't belong to a stop row
            stop_by_row[r].append(" ".join(w[4] for w in ws))

    # cells: time -> (row, col); other grid words -> notes
    cells = {}   # (row, col) -> time
    notes = defaultdict(list)  # (row, col) -> [words]
    for w in words:
        if grid_top - 2 <= w[1] <= grid_bottom + 2 and w[0] >= first_col_x - 3:
            r, c = row_of(w[1]), col_of(w[0])
            if TIME_RE.match(w[4]):
                cells[(r, c)] = w[4]
            elif w[4] not in ("-", "–", "—"):
                notes[(r, c)].append(w[4])

    line, direction, day = detect_context(page, grid_top, doc_lines)
    # headers are sometimes printed on the previous page only: inherit the last
    # seen line/direction/day-type when this grid page has none of its own
    line = line or inherit[0]
    direction = direction or inherit[1]
    day = day or inherit[2]
    if not line and doc_lines:  # bare line number in the header, no route text
        for _, text in page_lines_above(page, grid_top - 4):
            if re.fullmatch(r"\d{1,3}", text.strip()) and text.strip() in doc_lines:
                line = text.strip()
                break
    direction = re.sub(r"\s*Linie\s+\d+\s*$", "", direction).strip()  # "Zellerau - Sanderau Linie 4" -> "Zellerau - Sanderau"
    prefix = f"{dk}_p{pno}b{bi}"

    # per-row time sequences for gap filling
    row_times = defaultdict(list)  # row -> sorted [(col, "HH:MM")]
    for (r, c), t in cells.items():
        row_times[r].append((c, t))
    for r in row_times:
        row_times[r].sort()

    row_notes = {r: " ".join(w for (rr, _), ws in notes.items() if rr == r for w in ws)
                 for r in row_times}

    # an inherited direction can be the REVERSE of this grid (header-less page):
    # if the grid starts at the direction's end terminus, flip the direction
    seqs = sorted(row_times.keys())
    if seqs and direction:
        first_stop = " ".join(stop_by_row.get(seqs[0], [])).strip()
        toks = [t.strip() for t in re.split(r"\s*[-–]\s*", direction) if t.strip()]
        if len(toks) >= 2 and toks[-1] in first_stop and toks[0] not in first_stop:
            direction = " - ".join(reversed(toks))
    route = direction                       # full route string, kept for reference
    direction = dest_of(direction)          # normalized destination

    dep_rows, trip_cols = [], defaultdict(list)
    named = sum(1 for r in sorted(row_times)
                if " ".join(stop_by_row.get(r, [])).strip())
    if named < len(row_times) * 0.5:
        # more than half the rows have no stop names: not a real timetable grid
        # (marketing/frequency pages) — skip the block
        print(f"  WARNING: skipped block {bi} on page {pno + 1} of {pdf_name}: "
              f"no stop names ({named}/{len(row_times)} rows)", file=sys.stderr)
        return [], [], tuple(inherit)
    for r in sorted(row_times):
        stop = " ".join(stop_by_row.get(r, [])).strip() or f"(row {r})"
        seq = row_times[r]
        note_all = row_notes.get(r, "")
        alle = ALLE_RE.search(note_all)
        bis = BIS_RE.search(note_all)
        bis_m = t2m(bis.group(1)) if bis else None
        for c, t in seq:
            trip_id = f"{prefix}c{c:02d}"
            dep_rows.append({
                "pdf_name": pdf_name, "page": pno + 1, "line": line,
                "direction": direction, "route": route, "day_type": day, "trip_id": trip_id,
                "stop": stop, "stop_seq": r, "departure_time": t,
                "estimated": 0, "notes": " ".join(notes.get((r, c), [])),
                "valid_from": valid_from,
            })
            trip_cols[(bi, c)].append((r, t, stop))
        # fill "usw." gaps in this row
        for i in range(len(seq)):
            c, t = seq[i]
            if not any("usw" in w.lower() for w in notes.get((r, c), [])):
                continue
            prev = seq[i - 1] if i > 0 else None
            nxt = seq[i + 1] if i + 1 < len(seq) else None
            if not prev:
                continue
            diffs = [t2m(seq[j][1]) - t2m(seq[j - 1][1]) for j in range(max(1, i - 6), i + 1)]
            cadence = int(ALLE_RE.search(note_all).group(1)) if alle else (
                Counter(diffs).most_common(1)[0][0] if diffs else None)
            if not cadence or cadence <= 0:
                continue
            start, end = t2m(prev[1]), t2m(nxt[1]) if nxt else None
            if bis_m is not None:
                end = min(end, bis_m) if end is not None else bis_m
            if end is None:
                grid_max = max(t2m(t) for _, t in seq)
                end = grid_max
            k, tmin = 0, start + cadence
            while tmin <= end and k < 200:
                k += 1
                dep_rows.append({
                    "pdf_name": pdf_name, "page": pno + 1, "line": line,
                    "direction": direction, "route": route, "day_type": day,
                    "trip_id": f"{prefix}c{prev[0]}e{k}", "stop": stop,
                    "stop_seq": r, "departure_time": m2t(tmin),
                    "estimated": 1, "notes": "usw.-filled",
                    "valid_from": valid_from,
                })
                tmin += cadence

    trip_rows = []
    for (b, c), entries in sorted(trip_cols.items()):
        entries.sort()
        trip_rows.append({
            "pdf_name": pdf_name, "page": pno + 1, "line": line,
            "direction": direction, "route": route, "day_type": day, "trip_id": f"{dk}_p{pno}b{b}c{c:02d}",
            "first_stop": entries[0][2], "last_stop": entries[-1][2],
            "first_time": entries[0][1], "last_time": entries[-1][1],
            "stops_served": len(entries), "valid_from": valid_from,
        })
    return dep_rows, trip_rows, (line, route, day)  # carry the FULL route for inheritance


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    import glob
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    if not pdfs:
        sys.exit(f"no PDFs in {PDF_DIR}")
    deps, trips = [], []
    doc_valid = load_doc_validity(REPO_ROOT)
    for pdf in pdfs:
        name = os.path.basename(pdf)
        dk = doc_key(name)
        valid_from, doc_lines = doc_valid.get(name, ("", []))
        # single-line document (e.g. "BMK Linie 5"): use its line when no header is found
        initial_line = doc_lines[0] if len(doc_lines) == 1 else ""
        doc = pymupdf.open(pdf)
        ngrid = 0
        ctx = (initial_line, "", "")  # last seen (line, direction, day_type), carried across pages
        for pno in range(len(doc)):
            page = doc[pno]
            res = parse_grid_page(name, pno, page, dk, valid_from, inherit=ctx, doc_lines=doc_lines)
            if res:
                ngrid += 1
                d, t, detected = res
                ctx = tuple(detected[i] or ctx[i] for i in range(3))
                deps += d
                trips += t
            else:
                # text page: it may carry the line/direction header for the NEXT
                # grid page (header printed one page earlier) — record it
                detected = detect_context(page, page.rect.height)
                ctx = tuple(detected[i] or ctx[i] for i in range(3))
        doc.close()
        est = sum(1 for d in deps if d["pdf_name"] == name and d["estimated"])
        print(f"{name}: grid pages={ngrid}, departures so far, estimated={est}")
    with open(os.path.join(OUT_DIR, "grid_departures.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["pdf_name", "page", "line", "direction", "route", "day_type",
                                           "trip_id", "stop", "stop_seq", "departure_time",
                                           "estimated", "notes", "valid_from"])
        w.writeheader()
        w.writerows(deps)
    with open(os.path.join(OUT_DIR, "trips.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["pdf_name", "page", "line", "direction", "route", "day_type",
                                           "trip_id", "first_stop", "last_stop", "first_time",
                                           "last_time", "stops_served", "valid_from"])
        w.writeheader()
        w.writerows(trips)
    print(f"total: {len(deps)} grid departures ({sum(1 for d in deps if d['estimated'])} estimated), {len(trips)} trips")


if __name__ == "__main__":
    main()
