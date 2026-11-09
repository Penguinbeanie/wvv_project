# WVV Data Engineering — Pipeline Plan

Status: planning document. Nothing has been ingested into ClickHouse yet (the only
existing DB content is the superseded PDF-parse test run, see below).

Companion documents:

- `docs/gtfs_data_model.md` — DDL and merge semantics of the schedule layer
  (bronze/silver/gold). This plan references it; schedule DDL lives there, not here.
- `docs/archive/` — write-ups of the initial approach (parsing the Fahrplan PDFs with
  pdftotext/PyMuPDF grid parsing; issues and fixes log). Superseded by the GTFS-archive
  and LLM approach; kept for reference.
- `docs/master_pjs.pdf` — seminar overview (domains, phases, deliverables).

## 1. Goal

Land all WVV mobility data as clean, typed, query-ready tables in ClickHouse:

- **Ist-Daten** — APC/AVL stop events (`full_api_data` Parquet),
- **Soll-Daten** — schedules: 2022–2025 from the DELFI GTFS archive, 2026 from the
  WVV timetable PDFs (LLM-assisted extraction),
- **Context** — Bavarian/school holidays, Würzburg events, lecture periods,
  pedestrian counters.

Consumers: ML training and statistical analysis (Domain 3) and traffic simulation
(Domain 2). Every table should be joinable via stable keys: stops by DHID, lines by
their GTFS route short name, dates by calendar.

## 2. Environment

| Component | Details |
|---|---|
| RustFS | Container `rustfs` (rustfs/rustfs:1.0.0), S3 API on `localhost:9000`, console `9001`. Bucket `wvv` — the single repository for all raw data. Credentials in `rustfs/.env` (`RUSTFS_ACCESS_KEY` / `RUSTFS_SECRET_KEY`). |
| ClickHouse | Container `clickhouse` (25.8 LTS), HTTP `8123`, native `9002`. Joined to the RustFS docker network, so `http://rustfs:9000` works from inside ClickHouse — the intended path for bucket loads, verified working. |
| Credentials action item | `clickhouse/.env` has a `CLICKHOUSE_PASSWORD` with a stray trailing character that does not match the running server (`users.d/default-user.xml`). Fix before others trip over it; commit neither file. Better: inject S3 credentials into ClickHouse via storage config (`/etc/clickhouse-server/conf.d/s3.xml`) so they stop appearing in query logs and SQL. |
| Compute | Parquet/CSV ingestion is pure ClickHouse. The GTFS ingest job and the 2026 PDF→LLM job run in a Python container or venv (PyMuPDF, HTTP inserts; the archived test run shows the loading pattern). |

## 3. Raw data — everything lives in the RustFS bucket `wvv`

```
wvv/
├── full_api_data/     201 Parquet objects — APC/AVL stop events, 40 lines, 2022–2026
├── Additional Data/    10 CSV files — holidays / events / lectures / pedestrian counters
├── Fahrplaene/         ~91 timetable documents (PDF + XLSX), 25 line folders
├── gtfs/               DELFI GTFS snapshot ZIPs 2022–2025         (to add — 3.4)
└── curated/            2026 schedule CSVs from the LLM extraction (to add — 5.3)
```

The bucket is the one raw source of truth. Upstream providers (DELFI archive, WVV
documents) are fetched into the bucket first; every pipeline step reads from the bucket.
This keeps everything auditable and re-runnable.

### 3.1 `full_api_data/` — APC stop events (primary facts)

- 201 objects, `data_<start>_<end>_line_<n>.parquet`. 177 files with data
  (~5.11M rows, ~1.36 GB); 24 empty placeholders (598 bytes, footer only — skip and
  log, don't load as zero-row lines: lines 23/24/41 in all years, plus scattered
  2/7/9/25/35/99).
- Coverage: 40 lines (1–5, 6–13, 16, 20–21, 23–29, 33–35, 41, 44, 53–55, 91–99, 214),
  2022-01-02 → 2026-12-31. Period granularity varies: full-year, half-year or quarter
  files per line.
- Per-period rows: 2022: 1,331,632 · 2023: 1,165,706 · 2024: 1,144,872 ·
  2025: 1,126,235 · 2026: 339,297 (partial? — see open questions).

Base schema (35 columns, all non-empty 2022–2025 files):

| Column | Parquet type | Notes |
|---|---|---|
| `stop_event_id` | Int64 | event key |
| `report_date` | DateTime64(9) | |
| `journey` | Int64 | trip/run id (~414 unique per line-year in a sample) |
| `quality_factor` | Int64 | APC quality flag; semantics undocumented |
| `departure_plan_journey`, `departure_journey` | DateTime64(9) | planned vs. actual departure of the run |
| `line`, `line_route`, `route` | Int64 | `line` = filename line; others internal route ids |
| `direction` | String | e.g. `A` |
| `day_type` | String | DIVA-style code, e.g. `K7=8~872` — needs decoding |
| `stop_sequence` | Int64 | stop index within journey |
| `station_number`, `station_short`, `station` | Int64/String | stop reference (230 / `KÖNI` / `Königsberger Straße`) |
| `departure_hour_station`, `departure_plan_station` | DateTime64(9) | |
| `arrival_plan_door`, `departure_plan_door`, `arrival_plan_stop`, `departure_plan_stop` | DateTime64(9) | door/stop-level planned times |
| `vehicle_station` | Int64 | vehicle id |
| `vehicle_type` | String | e.g. `GTN` (tram type) |
| `cumsum_distance_plan` | Int64 | cumulative planned distance (m, presumably) |
| `cumsum_travel_time_actual` | Int64 | cumulative actual travel time (s, presumably) |
| `passenger_boarding`, `passenger_exiting`, `passenger_change`, `occupancy_departure` | Int64 | APC counters |
| `vehicle_utilization` | Float64 | |
| `passenger_boarding_measured`, `passenger_exiting_measured` | Int64 | ~31% zeros in a 2022 sample — "not measured" vs. zero? |
| `passenger_kilometer` | Float64 | |
| `main_date_day` | Date32 | service date |
| `weekday` | String | German (`Sonntag`) — redundant, drop in clean |

**Schema drift in the 40 files of 2026** (42 columns): `is_holiday` (Bool; typed
Parquet `null` in 2022–2025 files — ClickHouse schema inference fails there unless
`input_format_parquet_skip_columns_with_unsupported_types_in_schema_inference = 1`
or an explicit schema is supplied) plus pre-derived `day_group`, `time_shift`,
`next_station`, `next_station_short`, `edge`, `unique_journey`. Decide whether to
recompute those for 2022–2025 or version the column set.

### 3.2 `Additional Data/` — 10 context CSVs (comma-separated, except `dataAllStreets.csv`)

| File | Rows | Content |
|---|---|---|
| `bavarian_public_holidays.csv` | 128 | per-holiday intervals: `date, name, regionalScope, temporalScope, nationwide, subdivisions` |
| `bavarian_public_holidays_daily.csv` | 2,922 | daily 0/1 flags, 2019-01-01 → 2026-12-31 |
| `bavarian_school_holidays.csv` | 57 | interval rows `name, startDate, endDate, type, subdivisions` (BY) |
| `bavarian_school_holidays_daily.csv` | 2,922 | daily 0/1 flag |
| `events.csv` | 960 | Würzburg events 2019-03-03 → 2025-12-23: `name, start, end, concert` |
| `events_daily.csv` | 70,105 | hourly expansion (inconsistent with the daily files) |
| `lectures.csv` | 30 | university lecture periods 2018-10-01 → 2026-02-06: `start, end, jmu, thws` |
| `lectures_daily.csv` | 2,616 | daily JMU flag (THWS not expanded) |
| `verkaufsoffene_sonntage.csv` | 12 | shopping Sundays 2024+: `date, name, description` |
| `dataAllStreets.csv` | 83,838 | pedestrian counters, **semicolon-delimited**, hourly, 3 streets, 2019-04-02 → 2024-09-29 |

Quality notes: `dataAllStreets.csv` is the only `;` file and carries `+0200`-style
timezones separately from `date`+`hour`. Interval→daily expansion pairs are
inconsistent (`events_daily` is hourly, `lectures_daily` drops THWS) — load the
**interval** tables and expand calendars in SQL. Keys contain spaces, so URL-encode
`Additional%20Data` in S3 URLs.

### 3.3 `Fahrplaene/` — timetable documents (2026 source + reference)

One folder per line (1-2-3-4-5, 6, 8, 10, 12, 13, 16, 20, 21, 26–29, 33, 34, 91–99,
214), versioned documents, validity dates in the filenames. ~65 published PDF timetables
(incl. Baustellenfahrpläne, SEV plans, Straba bundles) and ~26 BMK XLSX workbooks.

Role in the pipeline:

1. **2026 schedule extraction** — the documents valid in 2026 are the source for the
   2026 timetable (section 5.3). PDFs only; the XLSX workbooks are out of the extraction
   path (2022–2025 is covered by GTFS; they remain as potential cross-check).
2. **Historical reference** — for 2022–2025 nothing is parsed systematically; printed
   PDFs serve as spot-check material for GTFS content (this has worked: the 2023
   construction-summer check, see 3.4).

### 3.4 `gtfs/` — DELFI GTFS snapshots 2022–2025 (to be loaded into the bucket)

- Upstream: `https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten (GTFS)/` —
  weekly full-Germany snapshot ZIPs, 2022 → present. Store them unmodified under
  `wvv/gtfs/<snapshot_date>.zip`.
- Local sample (unpacked): `../20250106_fahrplaene_gesamtdeutschland_gtfs` — 13 txt
  files, ≈ 6.5 GB unpacked, `stop_times.txt` alone 2.6 GB. Filtering to WVV is
  mandatory, never load full-Germany tables.
- Feed validity per snapshot from `feed_info.txt` (sample: 2024-12-21 → 2025-06-14).
- **WVV filter** (verified on the sample): `agency_id = 13346` ("Würzburger
  Straßenbahn", `Europe/Berlin`). 96 routes in the sample, incl. trams (`route_type 0`),
  buses (`route_type 3`), AST (`route_type 700`) and SEV replacement routes
  (`route_short_name` `4 SEV`, `5 SEV`). Stop space to keep: `de:09663:*` (Würzburg)
  plus surrounding `de:0967x:` where WVV lines leave the city.
- **Line dimension**: `route_short_name` / `route_long_name` from this feed are the
  unique, stable line numbers and names used across the whole project — not PDF
  headings or filenames.
- Ground truth: trip-per-trip comparison of the 2023 summer construction schedule
  (Straba 1/4 + SEV) against the printed Baustellenfahrplan showed 100% agreement —
  the feed includes construction and replacement-service schedules (details in
  `gtfs_data_model.md`).

## 4. Architecture

```
DELFI archive (upstream provider)
    └─ weekly ZIP snapshots 2022–2025 ── download ──► wvv/gtfs/          (raw copy in the bucket)

RustFS bucket wvv
    ├─ full_api_data/*.parquet ──────► ClickHouse s3() INSERT ─► raw.stop_events ─► clean.stop_events
    ├─ Additional Data/*.csv ────────► ClickHouse s3() INSERT ─► raw.* ─► dim.* / clean.pedestrian_counts
    ├─ gtfs/*.zip ───────────────────► Python ingest (WVV filter) ─► bronze_* ─► silver_* ─► gold_*
    └─ Fahrplaene/ (2026 PDFs) ──────► PyMuPDF (text + page raster)
                                          └─► DeepSeek v4.1 flash (schema + line list in prompt)
                                               └─► validated CSVs ─► wvv/curated/schedules_2026/
                                                    └─► bronze (source = 'pdf') ─► silver/gold
```

Design rules:

- Everything reads from the bucket; every product is reproducible from bucket contents.
- Provenance on every raw table: `source_file LowCardinality(String)` (idempotency key,
  delete-by-file before reload) and `loaded_at DateTime`.
- Bucket loads (Parquet/CSV) are pure ClickHouse `s3()` inserts — no intermediate tooling.
- The GTFS ingest job and the 2026 extraction job are Python (container or venv). Their
  outputs (curated CSVs) also land in the bucket, not on the host.

## 5. Data model

ClickHouse databases: `raw`, `clean`, `dim`, plus the schedule layer's bronze/silver/gold
(per `gtfs_data_model.md`).

### 5.1 Facts and context (raw → clean → dim)

**`clean.stop_events`** — `MergeTree`, `PARTITION BY toYYYYMM(main_date_day)`,
`ORDER BY (line, main_date_day, journey, stop_sequence)`. Cleaning steps per load:

1. Cast `Nullable` → non-nullable where safe; `DateTime64(9)` → `DateTime64(3, 'Europe/Berlin')`
   (confirm source timezone once).
2. Derive `weekday` from `main_date_day`; keep the German value only in raw.
3. Unify schema: superset of base + 2026 columns; for 2022–2025 recompute
   `is_holiday` (join `dim.public_holidays`), `day_group`, `time_shift`, `next_station`,
   `next_station_short`, `edge`, `unique_journey` so all years expose identical columns.
4. Reconcile `passenger_boarding` vs `passenger_boarding_measured` (and a derived
   `apc_measured` flag) once the semantics are clarified.
5. Per-batch validation: `stop_event_id` unique within file; `stop_sequence` monotonic per
   journey; `arrival_plan_stop <= departure_plan_stop`; no negative passenger counts.
6. Deduplicate across overlapping period files (full-year vs. quarter files for the same
   line-year — verify an overlap exists first; if so keep the finer file or use
   `ReplacingMergeTree` keyed on `stop_event_id`).

**Context/dimension tables** — `dim.public_holidays`, `dim.school_holidays`, `dim.events`,
`dim.lectures`, `dim.shopping_sundays`, `clean.pedestrian_counts`. Load the interval
CSVs; expand to daily/hourly calendars in SQL (a `cal.calendar` date table + joins), not
from the pre-expanded `_daily` files (inconsistent, partially redundant).

### 5.2 Schedules — bronze/silver per GTFS, gold as fingerprint model

DDL, merge semantics and the view catalog live in `docs/gtfs_data_model.md`. The
reasoning, as far as this plan is concerned:

**Silver keeps the GTFS structure — this is the right call.** The feed arrives fully
normalized; keeping bronze 1:1 with the GTFS files (+ `snapshot_date`) and silver in the
same shape makes ingest and cross-snapshot diffs mechanical and lossless. Two GTFS
specifics are handled in silver, not later:

- `calendar.txt` + `calendar_dates.txt` are resolved to concrete service dates exactly
  once (`silver_service_dates`); everything downstream works with dates.
- GTFS entity IDs are **unstable**: `route_id`/`trip_id`/`service_id` are re-invented on
  every export (verified: line 1 is `5316210_0` in the 2023 snapshot and
  `de:nvm:stwü|Straba|1:_0` in 2025). Joins across snapshots only via stable keys
  (`stop_id` = DHID, `agency_id`) or content fingerprints.

**Gold deviates from GTFS deliberately — the fingerprint model is appropriate.** GTFS has
no concept of identity across exports, so gold re-keys everything on content: a trip is
`fingerprint = cityHash64(line, direction, stops, times)` at grain
`(fingerprint, service_date)`. Why this works for us:

1. A physical trip sits in 10–20 consecutive snapshots; the fingerprint grain dedups that
   without losing evidence (silver keeps every observation).
2. `argMax(..., snapshot_date)` gives an effective truth with a full audit trail — a
   mid-period timetable correction overwrites the first publication, both remain.
   `snapshot_count` is a free confidence measure; `was_corrected` flags the outliers.
3. Stops keep append-only history (`silver_stop`), gold holds the current state via
   `first_seen`/`last_seen` lifecycle — no UPDATE/DELETE anywhere.
4. `stop_ids`/`dep_minutes` arrays are compact and ClickHouse-native and give ML/simulation
   direct access to the whole journey per row.
5. Bavarian holiday/school flags come from an external `ref_calendar` — correct, because
   the WVV operating pattern follows exactly these flags.

Refinements to fold into the DDL in `gtfs_data_model.md` before implementation:

1. **Keep arrival times.** `bronze_stop_times` has `arrival_min`, but `silver_trip` and
   `gold_trip_day` currently carry only `dep_minutes` — simulation needs dwell/arrival
   at timing points. Add `arr_minutes` alongside `dep_minutes`.
2. **Self-describing fingerprints.** `direction_id` (0/1) alone can flip meaning across
   route re-plannings; include the headsign/terminus in the fingerprint payload
   (fingerprint, plus the human-readable components stored separately for debugging).
3. **Make `gold_line` required, not optional.** Simulation needs the network dimension:
   line → `route_type` (tram/bus/AST/SEV), agency, first/last seen.
4. **Versioned `gold_stop`.** `ReplacingMergeTree ORDER BY stop_id` without a version
   column makes "current" dependent on insert order — add `snapshot_date` as the version
   and read via `argMax`, matching the gold merges elsewhere.
5. **Denormalized calendar flags on `gold_trip_day`** duplicate `ref_calendar` — fine for
   ML convenience, document it as derived.

### 5.3 Schedule year 2026 — Fahrplan PDFs via LLM extraction

The archive's snapshots do not cover 2026 (2025 snapshots reach only months into 2026 —
verify the newest one, open question 6). The 2026 timetable therefore comes from the
`Fahrplaene/` PDFs. PyMuPDF is used **only** for text extraction and rasterization; the
LLM does the table recognition:

1. **Input**: 2026-valid PDFs from `wvv/Fahrplaene/`. Validity parsed from filename and
   cover text (the phrasings and strategies that worked are documented in
   `docs/archive/fahrplaene_pipeline_issues_and_fixes.md`, issue 14).
2. **Preprocess (PyMuPDF)**: per page, layout-preserving text + a rasterized page image
   (PNG, ~150–200 dpi). No grid parsing, no OCR, no coordinate clustering.
3. **Extract (DeepSeek v4.1 flash, multimodal)**: one request per page with (text,
   image) plus a **fixed extraction contract** in the prompt:
   - target CSV schema mirroring the schedule model (line, direction, day_type,
     one row per (trip, stop_sequence, stop, arrival, departure), footnotes),
   - the **fixed line list** — line numbers and names from the GTFS-derived line
     dimension (3.4), with expected route descriptions/termini,
   - the known WVV stop names (from `silver_stop`) for normalization, with a fuzzy
     best-match and an `unmapped_stop` escape label.
4. **Glue code, not trust**: model output is converted to CSV deterministically and
   nothing is loaded unvalidated. CSVs are written to `wvv/curated/schedules_2026/`.
5. **Validation per document** (hard reject → review queue; silently accept nothing):
   - time cells match `HH:MM` / GTFS-style minutes past 24:00;
   - stops resolve against the reference list (residual unmapped list reviewed once);
   - trips have ≥ 2 stops, monotone `stop_sequence`, non-decreasing times;
   - day_type ∈ {Mon-Fri, Sat, Sun-Hol, School, special}; ambiguous → re-prompt first;
   - cross-check against 2026 `full_api_data`: planned departures
     (`departure_plan_station`) should find scheduled counterparts per line/direction.
6. **Load into the same model**: each document is treated as a *pseudo-snapshot*
   (`snapshot_date` = publication/validity date, `source = 'pdf'`), producing exactly the
   same bronze → silver → gold path as GTFS. Because gold is keyed on content
   fingerprints, PDF trips and GTFS trips meet in one table — an APC journey matches a
   GTFS fingerprint in 2022–2025 and a PDF-derived fingerprint in 2026. PDF-derived
   rows stay flagged by source; they are evidence from one document, not snapshot
   consensus, so their `snapshot_count` semantics differ.

Acceptance check (both schedule sources): for sample dates, every APC journey finds a
matching scheduled trip in the applicable timetable (template: the 2023
construction-summer comparison). This unlocks schedule-adherence analysis
(`departure_plan_station` vs. printed plan) and simulation inputs.

## 6. Execution phases

| Phase | Content | Depends on |
|---|---|---|
| 0. Housekeeping | Fix `clickhouse/.env` password; ClickHouse S3 storage config; APC semantics questions to data owner | — |
| 1. Raw Parquet load | `raw.stop_events` from 177 non-empty files, explicit schema (handles the null-typed `is_holiday`), skip-and-log empties | 0 |
| 2. Clean fact layer | `clean.stop_events` unified schema, validation, dedup; row-count reconciliation per line/year vs. 3.1 | 1 |
| 3. Context/dimensions | interval tables → `dim.*`, `clean.pedestrian_counts`; SQL calendar expansion | 0 |
| 4. GTFS ingest 2022–2025 | Download snapshots → `wvv/gtfs/` → registry, WVV filter, bronze → silver → gold per `gtfs_data_model.md` (incl. DDL refinements from 5.2) | 0, Python tooling |
| 5. Schedule 2026 via PDF + LLM | PyMuPDF text/raster → DeepSeek extraction → validation → `wvv/curated/schedules_2026/` → same bronze/silver/gold path | 4 (shared schema, line list, stop list) |
| 6. Analytics readiness | Join views (stop events × calendar × events × schedules), dataset exports for ML/simulation | 2, 3, 4, 5 |

## 7. Open questions

1. Are the 24 empty Parquet files "line didn't run" or export failures? (23/24/41 empty in every year.)
2. Do period files overlap (full-year vs. half/quarter files of the same line-year)? One check before designing dedup.
3. Semantics of `quality_factor`, `passenger_*_measured` vs `passenger_*`, `day_type` codes (`K7=8~872`), units of `cumsum_*`.
4. Source timezone of Parquet timestamps (local vs. UTC) — the street CSV carries `+0200`, the Parquets nothing.
5. Is 2026 APC partial (339k rows vs. ~1.1M in 2025) — a live feed? Decides incremental vs. full reload.
6. How far does the newest DELFI snapshot reach into 2026 (`feed_end_date`)? Decides how much 2026 needs the PDF path.
7. Does `full_api_data.line` map 1:1 to GTFS `route_short_name` (incl. SEV labels)? One join check after phase 4.
8. DeepSeek API practicalities: structured-output guarantees, per-request page/image limits, cost for a worst case of ~65 documents × ~30 pages. Fallback model needed?

## 8. Verification methods (what was checked so far)

- Bucket inventory via the RustFS data volume + ClickHouse `s3()` `LineAsString`
  (`_file`, `_size`, row counts) — Parquet, Fahrplan and CSV counts and sizes in this
  document come from there.
- Parquet schemas via `DESCRIBE TABLE s3(..., 'Parquet')` with the inference setting:
  142 files → 35 columns, 35 files → 42 columns, 0 failures; 24 empties by size.
  Null-profile and sample-row queries on the 2022 line-1 file.
- All 10 context CSVs: headers, samples, date ranges via aggregate queries.
- Two Fahrplan documents fetched and inspected (XLSX unzipped, PDF streams inflated):
  text-based, not scanned; embedded fonts partially lack `ToUnicode` maps (relevant
  only to the retired parsing approach; the LLM sees the rasterized page anyway).
- DELFI sample snapshot inspected locally (headers of all 13 files; agency 13346
  present, 96 routes incl. SEV; `feed_info` validity 2024-12-21 → 2025-06-14;
  quoted + CRLF fields; sizes).
- 2023 construction-summer GTFS↔PDF trip comparison: 100% agreement (documented in
  `gtfs_data_model.md`).
- Nothing was written to RustFS or ClickHouse in this planning phase; downloaded
  samples lived in `/tmp` only.
