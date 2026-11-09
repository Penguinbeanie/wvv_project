# Fahrplaene Pipeline — Issues & Fixes Log

Companion to `docs/fahrplaene_extraction.md` (pipeline design and transformations).
This document records every problem found during the test-run development of the
`scripts/fahrplaene/` pipeline, its root cause, the fix, and where the fix lives —
so the reasoning does not get lost when parsing additional documents or folders.

Pipeline state as of this writing: 9 PDFs (folder `1-2-3-4-5`) → 102,096 grid
departures (2,838 estimated), 5,106 trips, 14 routes, 22 document-validity
intervals across 7 ClickHouse tables in database `wvv`.

Run everything with:

```bash
bash scripts/fahrplaene/run_all.sh          # optional: [PDF_DIR]
```

---

## Issue → Fix log

### Data model

| # | Issue | Root cause | Fix | Where |
|---|---|---|---|---|
| 1 | Trips were not linked across stops; every departure was a flat row | `pdftotext -layout` flattens the grid into characters with no geometry | Coordinate-based parsing with PyMuPDF: time words clustered by x into **columns (= trips)** and y into rows (= stops); `trip_id` per column | `02b_parse_grids.py` |
| 2 | `trip_id` like `p3c02` existed in every PDF — 252 rows across 7 documents for one id | id only encoded page+column | Globally unique, self-describing ids: `<doc_slug>_p<page>b<block>c<column>` (e.g. `linie_1_5_ab_14_09_2021_p3b0c02`) | `doc_key()` in `02b_parse_grids.py` |
| 3 | No validity information on trips — impossible to know when a timetable applies | Document dates were never propagated | `valid_from` parsed from each document and propagated onto every trip/departure row; `valid_until` = next document's `valid_from` for the same line; materialized in `fahrplaene_document_validity` | `05_validity.py`, `extract_validity()` in `02_parse_timetables.py` |
| 4 | Direction names inconsistent: "Zellerau - Stadtmitte - Hauptbahnhof - Sanderau" vs "Zellerau - Sanderau" are the same direction | PDFs print routes with varying verbosity | `direction` normalized to the **destination only** (last region after the final spaced dash); full printed route kept in the `route` column | `dest_of()` in `02b_parse_grids.py` |
| 5 | "Grombühl", "Grombühl/Unikliniken" and bogus "Kliniken" as three different directions for the same terminus | (a) hyphen inside "Uni-Kliniken" split the destination; (b) compound spellings differ per document | (a) split only on spaced dashes so compounds stay intact; (b) compound `X/Y` reduces to its main part (`Grombühl`); (c) safety net: routes that share the same end stop (ignoring `ab`/`an`) are merged, most frequent name wins | `dest_of()` + end-stop merge in `06_routes.py` |
| 6 | Large parts of timetables omitted behind "usw." / "alle 15 min bis 12:00" cells | German timetables compress repeated columns | Gap filling per stop row: cadence from `alle N min` when printed, else mode of consecutive differences before the gap; bounded by `bis HH:MM` or the next shown time; filled rows flagged `estimated = 1`, `notes = 'usw.-filled'` | `02b_parse_grids.py` (usw. section) |

### Header / context parsing

| # | Issue | Root cause | Fix | Where |
|---|---|---|---|---|
| 7 | Line 3's reverse direction was missing entirely | One PDF page holds **two grids** (forward top, reverse bottom); the parser merged them into one grid, doubling every trip's stops | Page split into grid blocks wherever the vertical row gap exceeds 25 pt; each block gets its own columns, context and trip ids (`b<block>`) | `GRID_BLOCK_GAP` + `parse_grid_block()` in `02b_parse_grids.py` |
| 8 | Grid pages whose header is printed on the *previous* page got empty line/direction (e.g. Baustellenfahrplan_2023 page 5, header on page 4) | Context was only detected per grid page | Context (line/route/day-type) carried across pages and blocks — **including text-only pages**, which now also update it | `parse_grid_page()` / `detect_context()` |
| 9 | Line numbers 26, 28, 30 … 40 appeared as lines in Baustellenfahrplan_2022 | Those were **page numbers**; the real header is `5 / SEV` | `N / SEV` headers recognized (`5 / SEV`, `4 / 5 / SEV` → first number); bare numbers only accepted if they match the document's known line numbers | `detect_context()` |
| 10 | Stop rows and phone numbers caught as directions ("Felix-Fechenbach-Haus - 09:47 …", "0931 - 36 886 886") | "no times in line" guard used the anchored full-match regex, so lines containing times passed it; phone lines look like routes | Guards use substring time detection (`ANY_TIME_RE`); direction candidates must contain letters and are checked against a marketing-phrase blocklist (App, VVM, umsteigen, …) | `detect_context()` |
| 11 | Header "2 Würzburger Straßenbahn GmbH   1" not recognized as line 1 | pdftotext/PyMuPDF merges page number + company name + line number into one text line | Trailing-number heuristic: a number at the end of a longer header line is paired with a nearby route line (y ≤ 14 pt) | `detect_context()` |
| 12 | Header-less reverse grids inherited the forward direction | Inheritance has no way to know the block runs the other way | Reversal heuristic: if the block's first stop contains the inherited route's *end* terminus (and not its start), the route is flipped | `parse_grid_block()` |
| 13 | Marketing/frequency pages (Straba-City-Takt) produced pseudo-grids whose "stops" were time runs | Those pages mimic grids but have no stop names | Time words and bare numbers can never become stop names; blocks where > 50 % of rows lack a stop name are skipped with a stderr warning | `parse_grid_block()`, `06_routes.py` QA |

### Validity extraction

| # | Issue | Root cause | Fix | Where |
|---|---|---|---|---|
| 14 | Baustellenfahrplan_2023's dates only worked by luck — its real cover shows the mangled "2 9.0 7. - 1 1.0 9.2 0 2 3" and, one page down, "Vom 29.07. bis 11.09.2023" | Original parser only knew `Gültig ab:` / `Gültig: X bis Y` / `AB` in the first 3,000 chars | Multi-strategy scan: de-space digit-soup before matching (mangled dates become parseable), `Vom X bis Y` with year inferred from the end date, whole-document scan as fallback, `ab DD.MM.YYYY` in the filename as last resort; `Stand:` kept separately as publication date | `extract_validity()` in `02_parse_timetables.py` |

### Infrastructure / loading

| # | Issue | Root cause | Fix | Where |
|---|---|---|---|---|
| 15 | ClickHouse HTTP rejected `03_schema.sql` ("Multi-statements are not allowed") | HTTP interface executes one statement per request | Schema applied statement-by-statement; comments stripped **before** splitting (a `--` comment containing `;` otherwise corrupts the split) | `04_load_clickhouse.sh` |
| 16 | Silent load failures (INSERT into a non-existent table "succeeded") | `curl` without `-f` returns 0 on HTTP errors | `curl -sf` + explicit failure exit in the loader; tables are dropped and recreated each run so schema changes always apply | `04_load_clickhouse.sh` |
| 17 | Pipeline could not run on host | No Python on host initially; later a venv (`/home/Kai/projects/.venv`, Python 3.15) was created | `run_all.sh` prefers the venv, falls back to system python3, then to a throwaway docker container (which pip-installs pymupdf) | `run_all.sh` |
| 18 | Intermediate files owned by root blocked re-runs | First parse ran inside docker as root | Data dir ownership fixed; venv python now runs on host so files stay user-owned | environment fix (one-off) |

### Repo hygiene (pre-pipeline)

| # | Issue | Fix |
|---|---|---|
| 19 | `clickhouse/.env` and `rustfs/.env` (real passwords) were committed and pushed | Removed from tracking, `.gitignore` covers `.env`/`.env.*` (keeps `.env.example`), initial commit amended so secrets never entered history, remote force-pushed, **passwords rotated** (they were briefly public) |

---

## Known limitations (open, by decision)

- **SEV documents have no numeric line** — ~555 trips with empty `line`. Tag
  `line='SEV'` downstream if you need them grouped.
- **Estimated (`usw.`-filled) departures are per stop row** — their synthetic trip
  ids are not linked across stops; filter `estimated = 0` for full-journey analysis.
- **`Straba-City-Takt.pdf` is a marketing-style overview** — its remaining grids
  are less reliable than the regular timetables; prefer the regular PDFs.
- **Validity intervals are line-granular from document dates**: same-day documents
  (the two SEV PDFs from 2024-07-29) produce zero-width intervals; documents
  without line info are assumed to cover every line in the folder.
- **Day-type labels**: pages/blocks inherit the last seen day type; a few
  boundary pages may carry the previous label.
- Cadence fill assumes the pattern before the gap continues; mid-gap service
  changes are not detectable from the printed cells.

## Verification habits (keep doing this)

- `06_routes.py` prints the full routes table every run — **read it**; it is the
  cheapest QA surface for the whole pipeline (14 rows now).
- Block-skip warnings on stderr point at pages that are not real timetables.
- Sanity queries after each pipeline change:
  - `SELECT line, direction, count() FROM wvv.fahrplaene_trips GROUP BY 1,2` — no unexpected line numbers, no direction variants of the same terminus
  - `SELECT countIf(line=''), countIf(direction='') FROM wvv.fahrplaene_trips` — only SEV rows should have empty line
  - one full trip: `... WHERE trip_id='<id>' ORDER BY stop_seq` — monotonic times, plausible stops

---

## Script & function reference

All scripts live in `scripts/fahrplaene/`. Data flow:

```
PDF_DIR/*.pdf
  └─ 01_extract_text.sh ──▶ data/fahrplaene_text/*.txt          (layout text)
  └─ 02_parse_timetables.py ─▶ data/fahrplaene_parsed/{documents,raw_pages,departures,footnotes}.csv
  └─ 02b_parse_grids.py ──▶ data/fahrplaene_parsed/{grid_departures,trips}.csv   (reads PDFs + documents.csv)
  └─ 05_validity.py ──────▶ adds valid_from/valid_until to grid_departures/trips + document_validity.csv
  └─ 06_routes.py ────────▶ routes.csv
  └─ 03_schema.sql + 04_load_clickhouse.sh ─▶ ClickHouse database `wvv`
```

`data/` is gitignored — every intermediate is regenerable from the PDFs.

### `run_all.sh` — orchestrator
Runs 01 → 02 → 02b → 05 → 06 → 03/04 in order. Picks the first available
Python: `/home/Kai/projects/.venv/bin/python` → system `python3` → throwaway
`python:3.13-slim` container (which pip-installs PyMuPDF). Optional argument
`[PDF_DIR]` selects the source folder (default: `.../Fahrplaene/1-2-3-4-5`).

### `01_extract_text.sh` — PDF → layout text
Runs `pdftotext -layout` on every `*.pdf` in the source folder. Layout mode
keeps the timetable columns aligned with spaces. Output feeds stage 02 and
doubles as the human-readable reference for any parsing question.

### `02_parse_timetables.py` — line-based parse (documents, raw pages, flat departures, footnotes)
Stdlib-only; parses the *text* files (not coordinates). Writes
`documents.csv`, `raw_pages.csv`, `departures.csv` (flat, no trip linkage —
superseded by stage 2b for analysis but kept as fallback), `footnotes.csv`.

| Function | What it does |
|---|---|
| `de_date_to_iso(m)` | `DD.MM.YYYY` → `YYYY-MM-DD` |
| `extract_validity(text, pdf_name)` | Validity window: `Gültig ab: X`, `Gültig: X bis Y`, `Vom X bis Y` (year from end date), `AB X`, digit-soup de-spacing, whole-text then filename fallback; also `Stand:` (publication date). Returns `(valid_from, valid_until, stand)` |
| `extract_title(lines, stem)` | Document title from page 1: skips date/contact/route/digit-fragment lines; falls back to a cleaned filename when the cover text is fragmented |
| `extract_lines(name)` | Line numbers from the filename (`1-2-3-4-5` → `1-5`; dates and years stripped) |
| `extract_doc_type(name, title)` | `Fahrplan` / `Baustellenfahrplan` / `SEV` / `City-Takt` |
| `daytype_of(line)` | Day label → `Mon-Fri` / `Sat` / `Sun-Hol` / `School` |
| `parse_document(path)` | Splits pages on form feed; state machine: direction headers set line/route, day labels set day type, stop rows unpivot times into flat departures; `X = …` lines become footnotes |
| `main()` | Globs the text dir, writes the four CSVs |

### `02b_parse_grids.py` — coordinate-based grid parse (trips with linkage) — **requires PyMuPDF**
The analysis-grade parser. Writes `grid_departures.csv` and `trips.csv`.

| Function | What it does |
|---|---|
| `cluster(values, gap)` | Generic 1-D clustering: sorted values grouped while the gap ≤ threshold |
| `t2m(t)` / `m2t(m)` | `HH:MM` ⇄ minutes-since-midnight (for cadence math) |
| `page_lines_above(page, y_limit)` | Structural text lines (block/line level) above a y position; fragments on the same visual row are merged |
| `detect_context(page, grid_top, doc_lines)` | Finds line number, route and day type above a grid block. Handles: "number + route" on one line, bare number paired with a nearby route line (must match known doc lines), trailing number in merged headers, `N / SEV` headers, route-only headers (SEV). Rejects lines with times, phone numbers, marketing phrases |
| `doc_key(pdf_name)` | Document slug for globally unique trip ids (`linie_1_5_ab_14_09_2021_…`) |
| `load_doc_validity(repo_root)` | Reads `documents.csv` → `pdf_name → (valid_from, [line numbers])` |
| `dest_of(route)` | Direction normalization: last region after the final *spaced* dash; compound `X/Y` reduces to `X` (fixes #4/#5) |
| `parse_grid_page(...)` | Splits the page's time rows into grid **blocks** (vertical gap > 25 pt — fixes #7), runs each block through `parse_grid_block`, carries context between blocks and back to the caller for the next page |
| `parse_grid_block(...)` | The core: clusters columns/rows within the block, assembles stop names from words left of the first time column (wrapped lines merged by nearest row; time words and bare numbers excluded), collects cell notes, inherits/detects context, flips reversed inherited routes, normalizes the destination, then emits one row per (trip column × stop) plus the `usw.` gap fills (`estimated = 1`). Skips blocks where > 50 % of rows lack stop names (fixes #13) |
| `main()` | Per PDF: parses every page, prints per-document stats, writes both CSVs |

Emission format: `trip_id = <doc_slug>_p<page>b<block>c<column>` for printed
columns, `…c<col>e<k>` for estimated gap-fill rows.

### `05_validity.py` — validity windows
Reads `documents.csv` + the two grid CSVs. For each line, orders documents by
`valid_from`; a document's `valid_until` is the next document's `valid_from`
for that line (empty = still valid). Documents without line info cover every
line in the folder. Rewrites `grid_departures.csv`/`trips.csv` with
`valid_from`/`valid_until` columns and writes `document_validity.csv`
(one row per document × line).

### `06_routes.py` — routes dimension + QA
Reads `grid_departures.csv`. Groups by (line, normalized direction); start/end
stop = most frequent min/max-`stop_seq` stop. QA: drops routes whose start/end
contain times or placeholders (warns), merges directions sharing the same end
stop (ignoring `ab`/`an`), then **prints the whole routes table** for review.
Writes `routes.csv`.

| Function | What it does |
|---|---|
| `norm_direction(d)` | Dash-variant normalization for grouping (`–`/`—` → ` - `) |
| `end_key(stop)` | `ab`/`an`-stripped, lowercased stop name for variant merging |
| `main()` | Build → QA-filter → merge → print → write |

### `03_schema.sql` — ClickHouse DDL
Creates database `wvv` and eight `MergeTree` tables: `fahrplaene_documents`,
`fahrplaene_raw_pages`, `fahrplaene_departures`, `fahrplaene_footnotes`,
`fahrplaene_grid_departures`, `fahrplaene_trips`, `fahrplaene_document_validity`,
`fahrplaene_routes` (all with `extracted_at DEFAULT now()`).

### `04_load_clickhouse.sh` — loader
Drops and recreates the tables (schema evolves; full reload is idempotent),
applies the schema statement-by-statement with comments stripped, loads each
CSV via `INSERT … FORMAT CSVWithNames` over HTTP `:8123` with
`input_format_null_as_default=1`, credentials from `clickhouse/.env`, `curl -sf`
so failures are loud. Prints final row counts.
