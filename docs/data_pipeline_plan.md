# WVV Data Engineering Pipeline — Inventory & Plan

Status: planning document only. No data has been moved, transformed, or written to ClickHouse.
Source of truth: RustFS S3 bucket `wvv` (all findings below were verified live against the bucket via
ClickHouse's `s3()` table function and signed S3 GETs; see "Verification methods").

---

## 1. Goal

Build a pipeline that lands all raw data from RustFS as clean, typed, query-ready tables in
ClickHouse to support ML model training and statistical analysis (passenger demand, punctuality,
occupancy modeling, correlation with events/holidays/pedestrian flows).

## 2. Environment (as found)

| Component | Details |
|---|---|
| RustFS | Container `rustfs` (rustfs/rustfs:1.0.0), S3 API on `localhost:9000`, console on `9001`. Bucket: `wvv`. Credentials in `rustfs/.env` (`RUSTFS_ACCESS_KEY` / `RUSTFS_SECRET_KEY`). |
| ClickHouse | Container `clickhouse` (25.8 LTS), HTTP on `8123`, native on `9002`. Already joined to the RustFS docker network, so `http://rustfs:9000` works from inside ClickHouse — this is the intended ingestion path and was verified working. |
| Password mismatch (action item) | `clickhouse/.env` contains a `CLICKHOUSE_PASSWORD` that does **not** match the password actually active in the running server (persisted in `users.d/default-user.xml`). The `.env` has a stray trailing character. Fix the `.env` before anyone else trips over it. Do not commit either file. |
| Host tooling gap | The host has no Python and no S3 client. Extraction jobs (PDF/XLSX) will need a container or a project venv; Parquet/CSV ingestion needs nothing beyond ClickHouse itself. |

## 3. Data inventory (bucket `wvv`)

```
wvv/
├── full_api_data/        201 Parquet objects — APC/AVL stop events, lines & years 2022–2026
├── Additional Data/      10 CSV files — calendar / events / lectures / pedestrian counters
├── Fahrplaene/           91 documents (PDF + XLSX) — line timetables, 25 line folders
└── __MACOSX/             macOS resource-fork junk + .DS_Store objects — exclude from ingestion
```

### 3.1 `full_api_data/` — Parquet stop-event data (primary fact source)

- **201 objects**, naming convention `data_<start_date>_<end_date>_line_<n>.parquet`
  (e.g. `data_2024-01-01_2024-12-31_line_41.parquet`).
- **177 files with data (~5.11M rows, ~1.36 GB)**; **24 files are empty placeholders**
  (exactly 598 bytes: valid Parquet footer + schema, zero rows). Empty by line: 23, 24, 41
  (all years), plus 2/7/9/25/35/99 in scattered years. These must be skipped or logged, not
  loaded as "zero rows of that line".
- Coverage: **40 lines** (1–5, 6–13, 16, 20–21, 23–29, 33–35, 41, 44, 53–55, 91–99, 214),
  **2022-01-02 → 2026-12-31**. Period granularity varies: some lines have full-year files, others
  are split into halves or quarters (e.g. `2023-07-01_2023-12-31_line_5`, `2024-04-01_2024-06-30_line_...`).

Per-period volumes (rows):

| Period | Files | Rows | Empty files |
|---|---|---|---|
| 2022 (full + H2) | 39 | 1,331,632 | 3 |
| 2023 (full + H2) | 39 | 1,165,706 | 3 |
| 2024 (full + Q2 + H2) | 41 | 1,144,872 | 7 |
| 2025 (full + H2) | 42 | 1,126,235 | 7 |
| 2026 (full) | 40 | 339,297 | 4 |

**Schema (base, 35 columns)** — every non-empty 2022–2025 file:

| Column | Parquet type | Notes |
|---|---|---|
| `stop_event_id` | Int64 | event key |
| `report_date` | DateTime64(9) | |
| `journey` | Int64 | trip/run id (sample: ~414 unique per line-year) |
| `quality_factor` | Int64 | APC quality flag; semantics need documentation |
| `departure_plan_journey`, `departure_journey` | DateTime64(9) | planned vs. actual departure of the run |
| `line`, `line_route`, `route` | Int64 | line = filename line; route/line_route internal route ids |
| `direction` | String | e.g. `A` |
| `day_type` | String | DIVA-style code, e.g. `K7=8~872` — needs decoding or mapping |
| `stop_sequence` | Int64 | stop index within journey |
| `station_number`, `station_short`, `station` | Int64/String | stop reference (e.g. 230 / `KÖNI` / `Königsberger Straße`) |
| `departure_hour_station`, `departure_plan_station` | DateTime64(9) | |
| `arrival_plan_door`, `departure_plan_door`, `arrival_plan_stop`, `departure_plan_stop` | DateTime64(9) | door/stop-level planned times |
| `vehicle_station` | Int64 | vehicle id |
| `vehicle_type` | String | e.g. `GTN` (tram type) |
| `cumsum_distance_plan` | Int64 | cumulative planned distance (meters, presumably) |
| `cumsum_travel_time_actual` | Int64 | cumulative actual travel time (seconds, presumably) |
| `passenger_boarding`, `passenger_exiting`, `passenger_change`, `occupancy_departure` | Int64 | APC counters |
| `vehicle_utilization` | Float64 | |
| `passenger_boarding_measured`, `passenger_exiting_measured` | Int64 | measured (vs. modeled?) counters — in a 2022 line-1 sample ~31% of rows had `passenger_boarding_measured = 0`; investigate whether 0 = "not measured" or genuinely zero boardings |
| `passenger_kilometer` | Float64 | |
| `main_date_day` | Date32 | service date |
| `weekday` | String | German (`Sonntag`) — redundant with date, standardize or drop |

**Schema drift — 2026 files have 7 extra derived columns** (42 columns total, all 35 base files are
2026; 142 files use the base schema):

- `is_holiday` (Bool) — in 2022–2025 files this column exists but is typed as Parquet `null`
  (all-null artifact of the pandas/pyarrow writer). ClickHouse schema inference **fails** on those
  files unless `input_format_parquet_skip_columns_with_unsupported_types_in_schema_inference = 1`
  is set, or a explicit schema is supplied. This is the single biggest mechanical gotcha of the load.
- `day_group` (Float64), `time_shift` (Float64), `next_station`, `next_station_short` (String),
  `edge` (String), `unique_journey` (String) — pre-derived enrichment already computed upstream
  for 2026. Decide: recompute these for 2022–2025 in the pipeline for consistency, or keep the
  column set versioned.

### 3.2 `Additional Data/` — 10 CSV context files (comma-separated, except `dataAllStreets.csv`)

| File | Rows | Coverage / content |
|---|---|---|
| `bavarian_public_holidays.csv` | 128 | 2019 →, per-holiday rows: `date, name, regionalScope, temporalScope, nationwide, subdivisions` |
| `bavarian_public_holidays_daily.csv` | 2,922 | daily 0/1 flags `date, public_holiday, nationwide` (2019-01-01 → 2026-12-31) |
| `bavarian_school_holidays.csv` | 57 | interval rows: `name, startDate, endDate, type, subdivisions` (BY) |
| `bavarian_school_holidays_daily.csv` | 2,922 | daily 0/1 flag `date, school_holiday` (2019 → 2026) |
| `events.csv` | 960 | Würzburg events 2019-03-03 → 2025-12-23: `name, start, end, concert` |
| `events_daily.csv` | 70,105 | **hourly** expansion: `date (hourly), event, concert` |
| `lectures.csv` | 30 | university lecture periods 2018-10-01 → 2026-02-06: `start, end, jmu, thws` |
| `lectures_daily.csv` | 2,616 | daily flag `date, lecture_period_jmu` (⚠ column only covers JMU; THWS flag from `lectures.csv` is not expanded here) |
| `verkaufsoffene_sonntage.csv` | 12 | shopping Sundays 2024+: `date, name, description` |
| `dataAllStreets.csv` | 83,838 | **pedestrian counter data, semicolon-separated** (`;`), 29 columns, hourly, 3 streets × Wuerzburg, 2019-04-02 → 2024-09-29. Columns: id, streetname, city, date, hour, timezone, weekday, pedestrians_count (total/towards/away, adult/child, zone 1–3 splits), temperature, weather_condition, incidents, collection_type |

Quality notes for the CSVs:

- `dataAllStreets.csv` is the only semicolon-delimited file; `timezone` values like `+0200` are
  separate from `date`+`hour`; weather/incidents are free text (`partly-cloudy-day`, `no_incident`).
- The interval→daily expansion pairs are inconsistent: prefer loading the **interval** tables
  (`*_holidays.csv`, `events.csv`, `lectures.csv`) and generating daily/hourly calendars in SQL,
  rather than trusting the pre-expanded files (`events_daily` is hourly while `*_daily` holiday
  files are daily; `lectures_daily` drops the THWS flag).
- File names/keys contain spaces (`Additional Data/`) — URL-encode as `Additional%20Data` in S3 URLs.

### 3.3 `Fahrplaene/` — 91 timetable documents (the transformation problem)

Structure: one folder per line (1-2-3-4-5, 6, 8, 10, 12, 13, 16, 20, 21, 26–29, 33, 34, 91–99, 214),
documents are versioned line timetables with validity dates in the filenames
(e.g. `Linie 12 ab 14.09.2021.pdf`, `BMK Linie 12_ab 12.09.2023.xlsx`,
`Linie 29_web ab 15.12.2023.pdf`). Two families:

1. **PDFs (~65)**: published line schedules (incl. `BMK ..._Web.pdf`, construction schedules
   `Baustellenfahrplan_*.pdf`, `Straba-*` tram bundles, SEV replacement-service plans).
   Verified by downloading and parsing two samples:
   - They are **text-based, not scanned** (produced with PDFCreator from the DIVA planning system;
     vector text + some embedded JPEGs for logos/maps) — OCR is *not* required as a primary path.
   - **Caveat:** embedded subset fonts largely lack `ToUnicode` maps (a 313 KB sample had 10
     embedded fonts, only 1 `ToUnicode`). Stop names extract cleanly, but digits for departure
     times come out as custom-encoded glyphs in some documents. Plan: per-document extraction
     validation (regex: every cell must match `HH:MM` or `HHMM`) with OCR fallback per page.
2. **XLSX workbooks (~26)**: `BMK Linie <n>_ab <date>.xlsx`, 4–5 MB each, one sheet per line
   (e.g. sheet "Linie 12"). Verified structure: classic German timetable matrix — stops as rows
   (e.g. `Busbahnhof`, `Barbarossaplatz`, `Europastern` …), departure times as columns, sections per
   day type (`Montag mit Freitag`, `Samstag`, `Sonn- und Feiertag`), course letters (`B`, `C`, `D`,
   `E`) with footnotes (`C = verkehrt nur an Schultagen …`), `an`/`ab` (arrive/depart) markers.
   These are the **highest-fidelity timetable source** and should be extracted first wherever an
   XLSX version of a line+validity exists; PDFs cover the lines/versions without XLSX
   (notably 27, 28, 33, 34, 92–99, 214 and all non-BMK print PDFs).

Both families must be parsed into the same target model (section 4.3). NoGTFS-Feed exists in the
bucket — the Fahrplan documents are the only schedule source.

### 3.4 Junk (exclude from ingestion)

- `__MACOSX/**` — macOS resource-fork files (`._*`) mirroring the Fahrplaene tree.
- `.DS_Store` objects at `Fahrplaene/.DS_Store` and top level.
- These should be ignored by prefix filter in every ingestion job (and ideally deleted from the
  bucket; not done in this planning phase).

## 4. Pipeline design

### 4.1 Architecture

Two ingestion paths, both landing in a raw layer first:

```
RustFS (wvv bucket)
  ├── full_api_data/*.parquet ───────► ClickHouse s3() INSERT ─► raw.stop_events ─► clean.stop_events
  ├── Additional Data/*.csv ─────────► ClickHouse s3() INSERT ─► raw.* context tables ─► dim.* / clean.*
  └── Fahrplaene/** .pdf/.xlsx ──────► Python extraction job (containerized) ─► parquet back to
                                        RustFS (curated prefix) ─► clean.timetable_* tables
```

- **Parquet/CSV:** pure ClickHouse — no intermediate tooling needed. Verified working with
  `s3('http://rustfs:9000/wvv/...', '<access>', '<secret>', 'Parquet')` from inside the
  clickhouse container. Credentials should be injected via `S3` storage config
  (`/etc/clickhouse-server/conf.d/s3.xml` with `RUSTFS_ACCESS_KEY`/`RUSTFS_SECRET_KEY`) so they
  stop appearing in query logs and SQL files; until then reference the `.env` files.
- **Fahrpläne:** Python job (pdfplumber/openpyxl + OCR fallback), running in a container or venv
  (the host currently has neither Python nor any S3 client). Output written back to RustFS as
  Parquet under a new curated prefix (e.g. `wvv/curated/timetables/`), then loaded with the same
  `s3()` path. This keeps the pattern uniform and makes extraction reproducible/auditable.

### 4.2 Database layout

```
raw   — unmodified loads (Nullable types kept, + provenance columns)
clean — typed, deduplicated, enriched tables used by analysts/ML
```

Provenance everywhere: add `source_file LowCardinality(String)`, `loaded_at DateTime` to every raw
table; `source_file` doubles as the idempotency key (delete-by-file before reload).

**`clean.stop_events` (proposal)**

- Engine: `MergeTree`, `PARTITION BY toYYYYMM(main_date_day)`, `ORDER BY (line, main_date_day, journey, stop_sequence)`.
- Cleaning steps per load:
  1. Cast: `Nullable` → non-nullable where safe; `DateTime64(9)` → `DateTime64(3, 'Europe/Berlin')`
     (verify source timezone is local time; `timezone` handling must be confirmed once).
  2. Drop/derive: `weekday` from `main_date_day` (English enum or `dayOfWeek()`), keep original German
     value in raw only.
  3. Unify schema: target superset of base + 2026 columns; for 2022–2025 files recompute
     `is_holiday` (join against `dim.public_holidays`), `day_group`, `time_shift`, `next_station`,
     `next_station_short`, `edge`, `unique_journey` so all years expose identical columns.
  4. Reconcile `passenger_boarding` vs `passenger_boarding_measured`: keep both + a boolean
     `apc_measured` derived from `quality_factor`/counter semantics once clarified with WVV docs.
  5. Validate per batch: `stop_event_id` uniqueness within file; `stop_sequence` monotonic per
     `journey`; `arrival_plan_stop <= departure_plan_stop`; negative passenger counts rejected.
  6. Deduplicate across overlapping period files (a line may appear in a full-year file *and*
     a quarter file — **verify overlaps before assuming**; if confirmed, keep the finer-grained
     file, or use `ReplacingMergeTree` keyed on `stop_event_id`).

**Context/dimension tables:** `dim.public_holidays`, `dim.school_holidays`, `dim.events`,
`dim.lectures`, `dim.shopping_sundays`, `clean.pedestrian_counts` (from `dataAllStreets.csv`,
semicolon-delimited, typed columns, timezone normalized). Load the **interval** CSVs and expand to
daily/hourly calendars via materialized views or a `cal.calendar` Date table with joins — the
pre-expanded `_daily` files are redundant and partially inconsistent (drop `events_daily`,
`lectures_daily`, the `*_daily` holiday files from the clean layer).

### 4.3 Fahrplan transformation (detailed plan)

Target model (same for PDF and XLSX):

```
timetable_versions   (version_id, line, valid_from, source_file, source_type)
timetable_courses     (course_id, version_id, direction, day_type, course_letter, footnotes)
timetable_stops       (course_id, stop_sequence, station_name, station_short (if mappable),
                       arrival_time, departure_time, is_an/is_ab marker)
```

Extraction procedure per document:

1. Parse filename → (line, valid_from date, kind). Encode in `timetable_versions`.
2. **XLSX first** (openpyxl): locate day-type sections, transpose the time matrix into rows;
   capture footnotes per course letter. 26 workbooks cover lines 5, 6, 8, 12, 13, 16, 20, 21, 26, 29, 95–98.
3. **PDF** (pdfplumber): extract words with positions, cluster into table rows by y-coordinate;
   per-document validation of time tokens (`^\d{1,2}[:.]?\d{2}$`); if >x% of time cells fail the
   pattern (custom-encoded fonts, see 3.3), route the page to OCR (tesseract, German) and merge.
   Construction/special schedules (`Baustellenfahrplan`, `SEV`, `Straba-City-Takt`) should be
   flagged as `kind = 'special'` and versioned separately — they are temporary validities, not
   the regular timetable.
4. Map stop names from the documents to `station_number` used in `full_api_data`
   (fuzzy matching + manual review list; the APC data has both `station` and `station_short`,
   documents use long names like `Barbarossaplatz`).
5. Output Parquet per document to `wvv/curated/timetables/`, then ClickHouse load.
6. Acceptance check per line: for a sample date, every journey in `full_api_data` should find a
   matching scheduled course in the applicable timetable version (schedule adherence analysis
   becomes possible: planned-from-doc vs. `departure_plan_station`).

Effort estimate: XLSX family ~2–3 days; PDF pipeline (incl. OCR fallback + per-doc validation)
~5–10 days, dominated by layout variance across ~65 documents.

### 4.4 Execution phases

| Phase | Content | Depends on |
|---|---|---|
| 0. Housekeeping | Fix `clickhouse/.env` password mismatch; decide on deleting `__MACOSX`/`.DS_Store`; document `quality_factor`/`day_type` semantics (ask data owner) | — |
| 1. Raw Parquet load | `raw.stop_events` from 177 non-empty files, explicit schema (handles the null-typed `is_holiday`), skip-and-log empties | 0 |
| 2. Clean fact layer | `clean.stop_events` with unified schema, validation, dedup; per-line/year row-count reconciliation vs. section 3.1 table | 1 |
| 3. Context/dimensions | holiday/event/lecture/shopping-Sunday dims + `clean.pedestrian_counts`; calendar expansion in SQL | 0 |
| 4. Timetable extraction | XLSX family → curated parquet → `timetable_*` tables | 0, container tooling |
| 5. Timetable PDFs | PDF extraction + OCR fallback + stop-name mapping | 4 (shared target model) |
| 6. Analytics readiness | Join views (stop events × calendar × events × timetable versions), dataset exports for ML | 2, 3, 5 |

### 4.5 Open questions

1. Are the 24 empty Parquet files empty because the line didn't run, or export failures? (Lines 23/24/41 are empty in *every* year — suspicious for export gaps.)
2. Do period files overlap (full-year vs. half-year files for the same line-year)? Needs one overlap check before dedup design.
3. Exact semantics of `quality_factor`, `passenger_*_measured` vs. `passenger_*`, `day_type` codes (`K7=8~872`), units of `cumsum_*`.
4. Source timezone of the timestamps (local `Europe/Berlin` vs. UTC) — `dataAllStreets.csv` explicitly carries `+0200` offsets, the Parquet files carry no tz.
5. Meaning of "BMK" (from the WVV/DIVA planning office; the workbooks are the same content as the published PDFs).
6. Is 2026 data partial (only 339k rows so far vs. ~1M in earlier years) — i.e., a live feed that will keep growing? Affects whether the pipeline needs incremental loading.

## 5. Verification methods (what was actually checked)

- Full object inventory of the bucket via the RustFS data volume + ClickHouse `s3()` with
  `LineAsString` (`_file`, `_size`, row counts): `/tmp/api_files.tsv` (201 Parquet objects),
  `/tmp/fahrplaene.tsv` (91 Fahrplan documents), CSV row counts per file.
- Schema of every non-empty Parquet file via `DESCRIBE TABLE s3(..., 'Parquet')` with
  `input_format_parquet_skip_columns_with_unsupported_types_in_schema_inference=1`:
  142 files → 35 columns, 35 files → 42 columns, 0 failures; 24 empty files identified by size.
- Sample row + null-profile query on `data_2022-01-01_2022-12-31_line_1.parquet` (219,212 rows,
  414 journeys, 23 stations, no nulls in key columns, 31% `passenger_boarding_measured = 0`).
- CSV headers + samples of all 10 `Additional Data` files; date ranges via aggregate queries.
- Two Fahrplan documents fetched via SigV4-signed S3 GET and inspected: XLSX unzipped
  (sheet names, shared strings → stop names, day-type sections) and PDF streams inflated
  (text-based, fonts list, `ToUnicode` count).
- Nothing was written to RustFS or ClickHouse; downloaded samples lived in `/tmp` only.
