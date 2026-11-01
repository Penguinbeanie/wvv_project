# Fahrpläne Extraction — Test Run (folder `1-2-3-4-5`)

Status: working test pipeline. All steps are scripted and repeatable (see below).
Source folder: `/mnt/c/Users/spaie/Downloads/Fahrplaene/Fahrplaene/1-2-3-4-5` (9 PDFs;
the folder also contains one XLSX, `BMK-Linie 5 ab 07.03.2022.xlsx`, not covered here).

## Pipeline (run everything)

```bash
bash scripts/fahrplaene/run_all.sh [PDF_DIR]   # PDF_DIR optional, defaults to the 1-2-3-4-5 folder
```

| Step | Script | What it does |
|---|---|---|
| 1 | `scripts/fahrplaene/01_extract_text.sh` | `pdftotext -layout` on every PDF → `data/fahrplaene_text/*.txt` (layout mode keeps the timetable grid columns aligned) |
| 2 | `scripts/fahrplaene/02_parse_timetables.py` | Line-based parse of the text files into CSVs in `data/fahrplaene_parsed/` (documents, raw pages, flat departures, footnotes). Stdlib-only |
| 2b | `scripts/fahrplaene/02b_parse_grids.py` | Coordinate-based grid parse with **PyMuPDF** (`import pymupdf`): words with x/y positions → columns = trips, rows = stops. Needs `pip install pymupdf` (venv at `/home/Kai/projects/.venv` has it; docker fallback installs it) |
| 3 | `scripts/fahrplaene/03_schema.sql` | ClickHouse DDL, applied statement-by-statement over the HTTP interface (ClickHouse rejects multi-statement bodies; comments are stripped first) |
| 4 | `scripts/fahrplaene/04_load_clickhouse.sh` | Truncates the tables and loads the CSVs via `INSERT ... FORMAT CSVWithNames` over HTTP on `:8123`, credentials from `clickhouse/.env`. Idempotent — safe to re-run |

`data/` is gitignored: text/CSV intermediates are regenerable, only the scripts are committed.

## ClickHouse tables (database `wvv`)

| Table | Rows (this run) | Content |
|---|---|---|
| `wvv.fahrplaene_documents` | 9 | One row per PDF: `pdf_name`, `title`, `doc_type` (Fahrplan / Baustellenfahrplan / SEV / City-Takt), `lines`, `valid_from`, `valid_until`, `stand`, `pages` |
| `wvv.fahrplaene_raw_pages` | 262 | Verbatim text of every PDF page (`page`, `text`) — full-fidelity landing zone |
| `wvv.fahrplaene_departures` | 102,900 | Unpivoted timetable grid: one row per (document, line, direction, day_type, stop, departure_time); `notes` keeps cell annotations (`ab`, `usw.`, `alle 15 min`, …) |
| `wvv.fahrplaene_footnotes` | 40 | Legend lines parsed from `X = ...` rows (e.g. `A = endet Hauptbahnhof/West`, `S = verkehrt nur an Schultagen`) |
| `wvv.fahrplaene_grid_departures` | 100,907 (748 estimated) | Coordinate-based grid cells: one row per (trip column × stop row), with `trip_id`, `page`, `stop_seq`, `estimated` flag, `notes` |
| `wvv.fahrplaene_trips` | 3,406 | One row per real trip column: first/last stop and time, stops served |

All tables are `MergeTree`; `extracted_at` is set on insert.

## Stage 2b — grid parsing with trip linkage (`02b_parse_grids.py`)

1. A page with ≥ 8 `HH:MM` words is a grid page. Time words are clustered by x (gap > 10 pt) into **columns** and by y (gap > 5 pt) into **rows**.
2. **Column = trip**: `trip_id = <doc_slug>_p<page>b<block>c<column>` (e.g. `linie_1_5_ab_14_09_2021_p3b0c02`) — globally unique across all documents (verified: no trip_id maps to more than one pdf), so `fahrplaene_grid_departures` and `fahrplaene_trips` join on `trip_id` alone. A page can hold several grids (forward + reverse direction); the time rows are split into blocks wherever the vertical gap exceeds 25 pt, and each block gets its own columns, context and trip ids (`b<block>`). Querying one trip ordered by `stop_seq` yields the full stop-to-stop journey.
3. **Stop names** are words left of the first time column; wrapped names are re-joined by assigning each text line to the nearest time row (≤ 8 pt).
4. Line/direction/day-type context comes from the header lines above the grid: same-line "number + route", bare number paired with a nearby route line by y-proximity (bare numbers must match the document's known line numbers — page numbers are rejected), a trailing number in a merged header, and `N / SEV` replacement-service headers (`5 / SEV`, `4 / 5 / SEV`). Lines containing times, phone numbers or marketing phrases are never used as context. The printed route is kept verbatim in the `route` column; the `direction` column is **normalized to the destination** — the last region after the final dash ("Zellerau - Stadtmitte - Hauptbahnhof - Sanderau" → "Sanderau") — so route variants across documents collapse to one direction per terminus. When a block has no header of its own, line/route/day-type are carried over from previous pages/blocks — including text-only pages — and an inherited route is flipped when the grid starts at the route's end terminus (reverse-direction grids on header-less pages). Remaining gaps: SEV documents have no numeric line (~568 trips with empty `line`, mostly SEV + City-Takt pages) — tag them `line='SEV'` downstream if needed.
5. **"usw." gap filling**: for each stop row, a cell containing `usw.` marks omitted trips. Cadence = `alle N min` if printed, else the mode of the consecutive time differences before the gap; a `bis HH:MM` note bounds the fill. Times are generated from last-shown + cadence up to first-shown-after (or `bis`), inserted with `estimated = 1`, `notes = 'usw.-filled'`, and synthetic trip ids `<doc_slug>_p<page>b<block>c<col>e<k>`. Example: Klingenstraße, line 3, page 9 — printed 10:44, 10:59, then filled 11:14, 11:29, 11:44, 11:59 … at 15-min cadence.

## Stage 6 — routes dimension (`06_routes.py`)

`wvv.fahrplaene_routes` holds one row per (line, direction) with `start_stop`, `end_stop` (taken from the min/max `stop_seq` of its trips), trip/document counts, and the validity span seen so far. Quality rules applied:

- `direction` is the normalized destination (see stage 2b); compound destinations like `Grombühl/Unikliniken` reduce to their main part, so variants collapse.
- Directions that share the same end stop (ignoring `ab`/`an` markers) are merged into one route; the most frequent direction name wins.
- Blocks where more than half the rows have no stop names are skipped as non-timetable pages (marketing/frequency overviews) with a stderr warning.
- Routes whose start/end "stops" contain times or placeholders are dropped with a warning.
- The final routes table is printed on every run — short enough to review each time.

## Stage 5 — validity windows (`05_validity.py`)

Every trip and grid-departure row carries `valid_from` / `valid_until` (Date, nullable):

- `valid_from` comes from the document, propagated from `documents.csv`. Extraction (`extract_validity` in `02_parse_timetables.py`) scans the first 3,000 chars, then the whole text, then the filename, and understands the phrasings actually found in these PDFs: `Gültig ab: X`, `Gültig: X bis Y`, `AB X`, `Vom 29.07. bis 11.09.2023` (year inferred from the end date), pdftotext digit-soup dates (`2 9.0 7. - 1 1.0 9.2 0 2 3` → 29.07.–11.09.2023, de-spaced before matching), and `ab DD.MM.YYYY` in the filename as last resort. `Stand: X` is kept separately as the publication date, not validity.
- `valid_until` = the `valid_from` of the **next-later document covering the same line**; empty/NULL if none (still valid). Documents without line info (SEV, Baustellenfahrplan) are assumed to cover every line in the folder. Intervals are also materialized per document×line in `wvv.fahrplaene_document_validity`.

Example (line 5): `Linie 1-5 ab 14.09.2021.pdf` valid 2021-09-14 → 2022-07-30, …, `Straba-Fahrplan_4-5_WEB-Daten.pdf` 2024-11-04 → 2025-04-28, `Straba_Linie_4_5_web.pdf` 2025-04-28 → open.

## Transformations applied (in `02_parse_timetables.py`)

1. **Page split** on form-feed; every page stored raw.
2. **Document metadata**: title from the first non-junk lines of page 1 (skips dates, contact blocks, route/overview lines, digit-fragment lines; falls back to a cleaned filename when the cover text is fragmented by pdftotext). Validity dates parsed from `Gültig ab:`, `Gültig: X bis Y`, `AB …`, `Stand: …` and normalized `DD.MM.YYYY` → ISO `Date`. Line numbers from the filename (dates/years stripped; `1-2-3-4-5` → `1-5`).
3. **Grid parsing**: state machine per document — a direction header (`<line> <route with dashes>`, no times) sets line/direction; a day-type label (`Montags-freitags`, `Samstag`, `Sonn- und Feiertag`, …) sets `day_type` (normalized to `Mon-Fri`/`Sat`/`Sun-Hol`/`School`); a stop row (name + 2+ spaces + cells) is split into cells, each `HH:MM` cell becomes one departure row, `-` cells are skipped, anything else (`ab`, `usw.`, …) goes to `notes`.
4. **Loading**: CSV → ClickHouse HTTP with `input_format_null_as_default=1` so empty cells become NULL.

## Content of this run

| PDF | Title | Type | Lines | Valid | Departures |
|---|---|---|---|---|---|
| Linie 1-5 ab 14.09.2021.pdf | Fahrplan 1-5 | Fahrplan | 1,5 | from 2021-09-14 | 16,653 |
| Straba_Linie_4_5_web.pdf | STRABA-FAHRPLAN LINIE 4 & 5 | Fahrplan | 4,5 | from 2025-04-28 | 5,489 |
| Straba-Fahrplan_4-5_WEB-Daten.pdf | STRABA-FAHRPLAN LINIE 4 & 5 | Fahrplan | 4,5 | from 2024-11-04 | 16,926 |
| Straba-City-Takt.pdf | Straba City Takt | City-Takt | — | from 2023-09-12 | 19,995 |
| Komplett BMK Linie 5 ab 29.07.2024.pdf | Baustellen-Fahrplan Straba 5 | Baustellenfahrplan | 5 | 2024-07-29 → 2024-09-09 | 6,389 |
| Komplett BMK SEV Grombühl ab 29.07.2024.pdf | Baustellen-Fahrplan SEV Grombühl | SEV | — | 2024-07-29 → 2024-09-09 | 3,246 |
| Komplett BMK SEV Zellerau ab 29.07.2024.pdf | Baustellen-Fahrplan SEV Zellerau | SEV | — | 2024-07-29 → 2024-09-09 | 3,974 |
| Baustellenfahrplan_2022_webversion.pdf | Baustellen-Fahrplan | Baustellenfahrplan | — | from 2022-07-30 | 12,849 |
| Baustellenfahrplan_2023_Gesamt.pdf | NEUE STRABA-GLEISE | Baustellenfahrplan | — | 2023-07-29 → 2023-09-11 | 17,379 |

## Known limitations (test-run scope)

- **Stage 2 (line-based)** no longer reconstructs trip columns — use stage 2b (`fahrplaene_grid_departures` / `fahrplaene_trips`) for that. `fahrplaene_departures` remains as the flat fallback.
- **Estimated (`usw.`-filled) trips are per-stop-row**: their synthetic trip ids are not linked across stops. Real printed columns are fully linked via `trip_id`.
- **Validity is per line, derived from document dates**: two documents starting the same day (e.g. the two SEV PDFs from 2024-07-29) produce zero-width intervals; rows with an empty `line` get the document-wide earliest `valid_until`. The "empty lines = all lines" assumption holds for this folder (lines 1–5) but should be revisited for the full 25-line set.
- Some pages still get an empty `line` (SEV grids have no numeric line; `Straba-City-Takt.pdf` is a marketing-style frequency overview whose direction labels are less reliable — prefer the regular timetable PDFs for analysis).
- Cell annotations (`ab`/`an` terminus markers, letters like `A`/`S`) end up in `notes` or occasionally glued to the stop name; the footnote legends are in `fahrplaene_footnotes`.
- Cover-page titles of the marketing-style PDFs (City-Takt, 2022 Baustellenfahrplan) can be fragmentary; those fall back to the cleaned filename.
- The XLSX in the folder is not processed.
- `pdftotext` (stage 1/2) is not a table extractor, so `fahrplaene_departures` can mis-split unusual grids; raw page text is always preserved in `fahrplaene_raw_pages` as the safety net.
