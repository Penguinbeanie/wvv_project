#!/usr/bin/env python3
"""02_parse_timetables.py — parse pdftotext -layout output of WVV Fahrplaene into CSVs.

Reads:  <repo>/data/fahrplaene_text/*.txt
Writes: <repo>/data/fahrplaene_parsed/{documents,raw_pages,departures,footnotes}.csv

Usage: 02_parse_timetables.py [REPO_ROOT]   (default: current working directory)

Parsing model (best-effort, documented in docs/fahrplaene_extraction.md):
  - pages are split on form-feed; every page is landed verbatim in raw_pages.csv
  - document metadata (title, type, lines, validity dates) is taken from the
    first page header lines + filename
  - timetable grids: a "direction header" line (line number + route with dashes,
    no times) sets current line/direction; a day-type label line sets the
    day type; a stop row (name followed by HH:MM cells) is unpivoted so each
    departure time becomes one row in departures.csv
"""
import csv
import glob
import os
import re
import sys

REPO_ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
TEXT_DIR = os.path.join(REPO_ROOT, "data", "fahrplaene_text")
OUT_DIR = os.path.join(REPO_ROOT, "data", "fahrplaene_parsed")

TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
ANY_TIME_RE = re.compile(r"\d{1,2}:\d{2}")
DIRECTION_RE = re.compile(r"^\s*(\d{1,3})\s+(\S.*(?:-|–).*)$")
FOOTNOTE_RE = re.compile(r"^\s*([A-ZÄÖÜ])\s*=\s*(.+)$")
DATE_DE_RE = r"(\d{2}\.\d{2}\.\d{4})"
DE_DATE_IN_NAME_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")

DAYTYPE_PATTERNS = [
    ("montags-freitags", "Mon-Fri"), ("montag-freitags", "Mon-Fri"),
    ("montags - freitags", "Mon-Fri"), ("werktag", "Mon-Fri"),
    ("samstag", "Sat"),
    ("sonn- und feiertag", "Sun-Hol"), ("sonn-/feiertag", "Sun-Hol"),
    ("feiertag", "Sun-Hol"),
    ("schultag", "School"),
]

SKIP_TITLE_HINTS = (
    "gültig", "stand:", "ab ", "vvm", "www.", "mail@", "haltestelle",
    "gewähr", "änderungen", "niederflur", "kontakt", "wvv.de",
    "nahverkehr", "telefon", "neu:",
)


def de_date_to_iso(m):
    d, mo, y = m.split(".")
    return f"{y}-{mo}-{d}"


def extract_validity(text, pdf_name=""):
    """Return (valid_from, valid_until, stand) as ISO strings or ''.

    Handles the phrasings seen in WVV PDFs:
      "Gültig ab: X" / "Gültig: X bis Y" / "AB X" / "Stand: X"
      "Vom 29.07. bis 11.09.2023" (year inferred from the end date)
      pdftotext digit-soup dates ("2 9.0 7. - 1 1.0 9.2 0 2 3" -> 29.07.-11.09.2023)
    Scans the first 3000 chars, then the whole text, then the filename as fallback.
    """
    vfrom = vuntil = stand = ""

    def scan(chunk):
        nonlocal vfrom, vuntil, stand
        # de-space digit runs so pdftotext digit-soup dates become parseable,
        # keeping dots intact ("2 9.0 7. - 1 1.0 9.2 0 2 3" -> "29.07.-11.09.2023")
        d = re.sub(r"(\d)\s+(?=\d)", r"\1", chunk)
        d = re.sub(r"\.\s*-\s*(?=\d)", ".-", d)
        m = re.search(r"Gültig ab:\s*(\d{2}\.\d{2}\.\d{4})", d, re.I)
        if m and not vfrom:
            vfrom = de_date_to_iso(m.group(1))
        m = re.search(r"Gültig:\s*(\d{2}\.\d{2}\.\d{4})\s*bis\s*(\d{2}\.\d{2}\.\d{4})", d, re.I)
        if m:
            vfrom, vuntil = de_date_to_iso(m.group(1)), de_date_to_iso(m.group(2))
        m = re.search(r"Vom\s+(\d{2}\.\d{2}\.)\s*bis\s*(\d{2}\.\d{2}\.(\d{4}))", d, re.I)
        if m and not vfrom:  # "Vom 29.07. bis 11.09.2023": year taken from the end date
            vfrom = de_date_to_iso(m.group(1) + m.group(3))
            vuntil = de_date_to_iso(m.group(2))
        m = re.search(r"\bAB\s+(\d{2}\.\d{2}\.\d{4})\b", d)
        if m and not vfrom:
            vfrom = de_date_to_iso(m.group(1))
        m = re.search(r"Stand:\s*(\d{2}\.\d{2}\.\d{4})", d, re.I)
        if m and not stand:
            stand = de_date_to_iso(m.group(1))
        if not vfrom:  # bare date range, e.g. digit-soup "29.07.-11.09.2023"
            m = re.search(r"(\d{2}\.\d{2}\.)(\d{4})?(?:\s*-\s*(\d{2}\.\d{2}\.))?(\d{4})", d)
            if m:
                y = m.group(2) or m.group(4)
                vfrom = de_date_to_iso(m.group(1) + y)
                if m.group(3):
                    vuntil = de_date_to_iso(m.group(3) + m.group(4))

    scan(text[:3000])
    if not vfrom:
        scan(text)  # validity note buried deeper in the document
    if not vfrom and pdf_name:  # last resort: date in the filename ("... ab 14.09.2021.pdf")
        m = re.search(r"ab\s+(\d{2}\.\d{2}\.\d{4})", pdf_name, re.I)
        if m:
            vfrom = de_date_to_iso(m.group(1))
    return vfrom, vuntil, stand


def extract_title(first_page_lines, pdf_stem):
    parts = []
    for raw in first_page_lines[:12]:
        line = raw.strip()
        if not line or len(line) < 2:
            continue
        low = line.lower()
        if any(h in low for h in SKIP_TITLE_HINTS):
            continue
        # skip digit-heavy fragments (pdftotext sometimes spaces out dates: "2 9.0 7. ...")
        digits = re.sub(r"\D", "", line)
        if len(digits) >= 5 and len(digits) / len(line) > 0.4:
            continue
        # skip route/overview lines: "1 Sanderau - Hauptbahnhof - ...", "Zellerau - Hauptbahnhof"
        if re.match(r"^\d+\s+\S", line) or re.search(r"\s-", line):
            continue
        parts.append(line)
        if len(parts) >= 3:
            break
    title = " ".join(parts)
    title = re.sub(r"-\s+(?=[A-ZÄÖÜ])", "-", title)  # STRABA- FAHRPLAN -> STRABA-FAHRPLAN
    title = re.sub(r"\s+", " ", title).strip()
    if any(len(tok) <= 2 and tok.isalpha() for tok in title.split()):
        # stylized cover text came out fragmented -> derive the title from the filename
        name = DE_DATE_IN_NAME_RE.sub(" ", pdf_stem)
        title = re.sub(r"[_\-]+", " ", name)
        title = re.sub(r"\s+", " ", title).strip()
    return title


def extract_lines(name):
    if "1-2-3-4-5" in name:
        return "1-5"
    cleaned = DE_DATE_IN_NAME_RE.sub(" ", name)
    nums = [n for n in re.findall(r"\d+", cleaned) if not YEAR_RE.match(n)]
    return ",".join(nums)


def extract_doc_type(name, title):
    hay = (name + " " + (title or "")).lower()
    if "sev" in name.lower():
        return "SEV"
    if "baustellen" in hay:
        return "Baustellenfahrplan"
    if "city-takt" in hay or "citytakt" in hay:
        return "City-Takt"
    return "Fahrplan"


def daytype_of(line):
    low = line.lower()
    for pat, label in DAYTYPE_PATTERNS:
        if pat in low:
            return label
    return None


def parse_document(txt_path):
    pdf_name = os.path.basename(txt_path)[:-4] + ".pdf"
    with open(txt_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    pages = text.split("\f")

    vfrom, vuntil, stand = extract_validity(text, pdf_name)
    title = extract_title(pages[0].splitlines(), os.path.basename(txt_path)[:-4])
    lines = extract_lines(pdf_name)
    doc_type = extract_doc_type(pdf_name, title)

    doc_row = {
        "pdf_name": pdf_name, "title": title, "doc_type": doc_type,
        "lines": lines, "valid_from": vfrom, "valid_until": vuntil,
        "stand": stand, "pages": len([p for p in pages if p.strip()]),
        "source_dir": os.path.dirname(txt_path),
    }

    raw_rows, dep_rows, note_rows = [], [], []
    cur_line, cur_dir, cur_day = "", "", ""
    for page_no, page in enumerate(pages, start=1):
        if page.strip():
            raw_rows.append({"pdf_name": pdf_name, "page": page_no, "text": page})
        for line in page.splitlines():
            if not line.strip():
                continue
            dt = daytype_of(line)
            if dt and not ANY_TIME_RE.search(line):
                cur_day = dt
                continue
            m = DIRECTION_RE.match(line)
            if m and not ANY_TIME_RE.search(line):
                cur_line = m.group(1)
                cur_dir = re.sub(r"\s+", " ", m.group(2)).strip()
                continue
            if not ANY_TIME_RE.search(line):
                fm = FOOTNOTE_RE.match(line)
                if fm:
                    note_rows.append({
                        "pdf_name": pdf_name, "code": fm.group(1),
                        "description": fm.group(2).strip(),
                    })
                continue
            # stop row: name ... 2+ spaces ... cells
            sm = re.match(r"^\s*(\D.*?)\s{2,}(.*\S)\s*$", line)
            if not sm:
                continue
            stop, rest = sm.group(1).strip(), sm.group(2)
            times, notes = [], []
            for cell in re.split(r"\s{2,}", rest):
                cell = cell.strip()
                if not cell:
                    continue
                if TIME_RE.match(cell):
                    times.append(cell)
                elif re.fullmatch(r"[-–—]+", cell):
                    continue
                else:
                    notes.append(cell)
            for t in times:
                dep_rows.append({
                    "pdf_name": pdf_name, "line": cur_line,
                    "direction": cur_dir, "day_type": cur_day,
                    "stop": stop, "departure_time": t,
                    "notes": " ".join(notes),
                })
    return doc_row, raw_rows, dep_rows, note_rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    docs, raws, deps, notes = [], [], [], []
    txts = sorted(glob.glob(os.path.join(TEXT_DIR, "*.txt")))
    if not txts:
        sys.exit(f"no .txt files in {TEXT_DIR} — run 01_extract_text.sh first")
    for t in txts:
        d, r, dep, n = parse_document(t)
        docs.append(d); raws += r; deps += dep; notes += n
        print(f"parsed {d['pdf_name']}: pages={d['pages']} departures={len(dep)}")

    def write(name, rows, fields):
        with open(os.path.join(OUT_DIR, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write("documents.csv", docs, ["pdf_name", "title", "doc_type", "lines",
                                  "valid_from", "valid_until", "stand", "pages", "source_dir"])
    write("raw_pages.csv", raws, ["pdf_name", "page", "text"])
    write("departures.csv", deps, ["pdf_name", "line", "direction", "day_type",
                                   "stop", "departure_time", "notes"])
    write("footnotes.csv", notes, ["pdf_name", "code", "description"])
    print(f"total: {len(docs)} documents, {len(raws)} pages, {len(deps)} departures, {len(notes)} footnotes")


if __name__ == "__main__":
    main()
