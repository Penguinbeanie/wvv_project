# Data Discovery — RustFS bucket `wvv` (verified inventory)

Status: **verified against the live bucket on 2026-11-18**. Every number below was
re-measured, not copied. This document checks the initial discovery claims in
`docs/data_pipeline_plan.md` §3, corrects where they were off, adds term-paper-relevant
context (provenance, formats, quality quirks), and gives copy-paste reproduction
queries plus references so you can reconfirm everything yourself.

Companion documents: `docs/data_pipeline_plan.md` (pipeline plan this verifies),
`docs/gtfs_data_model.md` (schedule-layer DDL), `docs/archive/` (retired PDF-parse
test run), `docs/paper_plan.md` + `docs/paper_sources/` (term paper).

---

## 1. How this was verified (reproduction)

Environment actually running (checked 2026-11-18):

- `rustfs` container (rustfs/rustfs:1.0.0), S3 API on `localhost:9000`, console `9001`,
  data in docker volume `wvv_project_rustfs-data` (host path
  `/var/lib/docker/volumes/wvv_project_rustfs-data/_data`, root-only; read via the S3
  API instead).
- `clickhouse` container (clickhouse/clickhouse-server:25.8, server version
  **25.8.33.6**), HTTP `localhost:8123`. **No S3 credentials are configured inside
  ClickHouse** (`/etc/clickhouse-server/conf.d/` is empty) — every query below passes
  them explicitly. Credentials live in `rustfs/.env` (`RUSTFS_ACCESS_KEY` /
  `RUSTFS_SECRET_KEY`); never commit them.
- ClickHouse reaches RustFS as `http://rustfs:9000` (shared `rustfs_default` docker
  network) — confirmed working.

All queries were run through ClickHouse's `s3()` table function over HTTP, e.g.:

```sql
-- list every object with size (LineAsString reads any bytes; _path/_file/_size are virtual columns)
SELECT _path, _size FROM s3('http://rustfs:9000/wvv/**','<AK>','<SK>','LineAsString','line String')
GROUP BY _path, _size ORDER BY _path;

-- row counts per year (explicit structure avoids inference issues)
SELECT substring(_file,6,4) AS yr, count(DISTINCT _file) AS files, sum(rows) AS rows
FROM (SELECT _file, count() AS rows FROM s3('http://rustfs:9000/wvv/full_api_data/*.parquet',
        '<AK>','<SK>','Parquet','stop_event_id Int64') GROUP BY _file)
GROUP BY yr ORDER BY yr;

-- schema of one parquet file (skip setting needed for 2022-2025 files, see §3.1)
DESCRIBE TABLE s3('http://rustfs:9000/wvv/full_api_data/data_2022-01-01_2022-12-31_line_1.parquet',
        '<AK>','<SK>','Parquet') SETTINGS input_format_parquet_skip_columns_with_unsupported_types_in_schema_inference=1;
```

Gotchas hit while verifying (all reproduced):

- Object keys contain spaces (`Additional Data/`) and non-ASCII UTF-8 (`Grombühl`) —
  URL-encode as `Additional%20Data`, and let the S3 client handle UTF-8 keys.
- Plain `CSV` format fails on the semicolon file and on multi-column comma files when
  read as one column; use `CSVWithNames` (inference) or pass `format_csv_delimiter=';'`
  plus an explicit structure for `dataAllStreets.csv`.
- `DESCRIBE` on 2022–2025 parquet fails with `Unsupported Parquet type 'null' of an
  input column 'is_holiday'` unless
  `input_format_parquet_skip_columns_with_unsupported_types_in_schema_inference=1`
  is set — exactly as `data_pipeline_plan.md` §3.1 predicted.
- The 24 empty parquet files (598 bytes, footer only) make `DESCRIBE` fail with
  `CANNOT_EXTRACT_TABLE_STRUCTURE` — skip-and-log them, don't load.
- ClickHouse HTTP interface: settings go as URL params
  (`http://default:default@localhost:8123/?input_format_...=1`), not a `SETTINGS` clause.
- `clickhouse/.env` note from the plan: the file currently contains
  `CLICKHOUSE_PASSWORD=default` with **no** trailing character (checked with `od -c`),
  and the running server's `users.d/default-user.xml` sets password `default` —
  `default:default` authenticates fine right now. The "stray trailing character"
  issue is not reproducible at the moment; re-check before others rely on compose env.

---

## 2. Bucket inventory (measured 2026-11-18)

421 objects total under `wvv/`:

| Prefix | Objects | Real content | Size |
|---|---|---|---|
| `full_api_data/` | 201 | 177 parquet with data + 24 empty placeholders (598 B each) | 1,360,487,425 B ≈ **1.36 GB** (1.27 GiB) |
| `Additional Data/` | 10 | 10 CSV context files | ≈ 17.4 MB (largest: `dataAllStreets.csv` 15.2 MB) |
| `Fahrplaene/` | 209 | **91 real documents** (61 PDF + 30 XLSX) in 25 line folders, **plus 117 macOS `._*` AppleDouble junk files + 1 `.DS_Store`** | ≈ 193 MiB (real docs) |
| `__MACOSX/` | 1 | `._Fahrplaene` junk (macOS metadata leaked into the bucket root) | 212 B |
| `gtfs/` | **0** | does not exist yet — DELFI snapshots still to be downloaded (§6) | — |
| `curated/` | **0** | does not exist yet — LLM-extracted 2026 schedules still to be produced | — |

Reproduce: `SELECT _path, _size FROM s3('http://rustfs:9000/wvv/**','<AK>','<SK>','LineAsString','line String') GROUP BY 1,2;`

**Data-quality note for the paper:** the bucket was uploaded from macOS — 118
`__MACOSX`/`._*` artifacts are stored alongside the real objects. Any loader must
filter keys matching `__MACOSX/` or basename starting with `._` (they would otherwise
double-count files / break parsers). Object keys with `ü` etc. are UTF-8.

---

## 3. Claim-by-claim check of `data_pipeline_plan.md` §3

| Plan claim | Verified result | Status |
|---|---|---|
| 201 parquet objects in `full_api_data/` | 201 objects | ✅ confirmed |
| 177 files with data, ~5.11M rows, ~1.36 GB | 177 non-empty files, **21,982,494 rows**, 1.36 GB | ⚠️ **row count corrected ~4.3×** — see §3.1 |
| 24 empty placeholders, 598 B, "lines 23/24/41 in all years, plus scattered 2/7/9/25/35/99" | 24 files × exactly 598 B. Empty lines per year: 2022: 23,24,41 · 2023: 23,24,41 · 2024: 7,9,23,24,25,35,41,99 · 2025: 2,7,9,23,35,41,99 · 2026: 2,7,23,41. **23 and 41 are empty in all 5 years; 24 is empty only 2022–2024 (it has data in 2025–2026)** | ⚠️ refined |
| 40 lines, coverage 2022-01-02 → 2026-12-31 | 40 line numbers exist as files (1–10, 12, 13, 16, 20, 21, 23–29, 33–35, 41, 44, 53–55, 91–99, 214); **38 have rows** (23, 41 are empty-only). Filename periods span 2022-01-01→2026-12-31, but **actual data ends 2026-04-06** (max `report_date`/`main_date_day` = 2026-04-06); min = 2022-01-01 | ⚠️ refined (2026 is partial — answers plan open question 5) |
| Per-year rows 2022: 1,331,632 · 2023: 1,165,706 · 2024: 1,144,872 · 2025: 1,126,235 · 2026: 339,297 | **2022: 5,787,537 · 2023: 4,907,775 · 2024: 5,014,518 · 2025: 4,954,950 · 2026: 1,317,714** (non-empty files: 36/36/34/35/36) | ❌ **corrected** — plan's numbers don't reproduce (see query in §1; `stop_event_id` is unique per row, so no hidden duplication explains the gap) |
| Base schema 35 columns, all non-empty 2022–2025 files | 142 files × 35 columns (2022: 36, 2023: 36, 2024: 34, 2025: 35, 2026: 1 — the exception is `data_2026-..._line_34.parquet`) | ✅ confirmed |
| Schema drift: 42 columns in the 40 files of 2026; 142→35 / 35→42 / 24 empty, 0 failures | 35 files × 42 columns (all 2026 except line 34), 24 empty; the `null`-typed `is_holiday` in 2022–2025 breaks inference without the skip setting (reproduced) | ✅ confirmed |
| 2026 adds `is_holiday`, `day_group`, `time_shift`, `next_station`, `next_station_short`, `edge`, `unique_journey` | Confirmed, exact inferred types: `is_holiday Nullable(Bool)`, `day_group Nullable(Float64)`, `time_shift Nullable(Float64)`, `next_station/next_station_short/edge/unique_journey Nullable(String)`. In a 2026 line-1 sample **~45.5% of rows have these NULL** | ✅ + extra detail |
| ~414 unique journeys per line-year in a sample | 2022 line-1 full-year file: 414 distinct `journey` | ✅ confirmed |
| ~31% zeros in `passenger_*_measured` (2022 sample) | 2022 line 1: 30.9% `passenger_boarding_measured=0`, 29.0% `passenger_exiting_measured=0`; 2026 line 1: 30.0% | ✅ confirmed |
| 10 context CSVs with the listed row counts | All 10 row counts match exactly (128 / 2,922 / 57 / 2,922 / 960 / 70,105 / 30 / 2,616 / 12 / 83,838 data rows) | ✅ confirmed |
| `dataAllStreets.csv` semicolon-delimited, `+0200` timezone, 3 streets, 2019-04-02→2024-09-29, 83,838 rows | Confirmed: `;`-delimited, 31 columns, 83,838 rows, 3 streets, 2019-04-02→2024-09-29. **Timezone column holds both `+0100` and `+0200` (DST-aware)**, not just `+0200`; `city` value is `" Wuerzburg"` with a leading space | ✅ + corrections |
| `Fahrplaene/`: ~91 documents, 25 line folders, ~65 PDF + ~26 XLSX | 25 folders ✅, **91 documents ✅ but split is 61 PDF + 30 XLSX** (plan's ~65/~26 was off); plus 118 junk files | ⚠️ refined |
| `gtfs/`, `curated/` "to add" | Both prefixes absent — confirmed nothing ingested yet | ✅ confirmed |
| Only existing DB content is the superseded PDF-parse test run | ClickHouse has exactly one user database `wvv` with 9 `fahrplaene_*` tables (test run): `fahrplaene_documents` 9, `fahrplaene_document_validity` 22, `fahrplaene_raw_pages` 262, `fahrplaene_routes` 14, `fahrplaene_trips` 5,106, `fahrplaene_footnotes` 40, `fahrplaene_departures` 102,900, `fahrplaene_grid_departures` 102,096, (9 tables total) | ✅ confirmed |

**Corrections to propagate** (this doc is the reference; update the plan/paper when convenient):

1. `data_pipeline_plan.md` §3.1 and `paper_plan.md` §2/§4 repeat "~5.11M APC rows" /
   "~1.1M rows/year" — the measured truth is **21,982,494 rows total, ~4.4–5.8M per
   year 2022–2025, 1.32M in 2026 (data only through 2026-04-06)**.
2. Coverage end is 2026-04-06 (not 2026-12-31); 2026 is a partial export (plan open
   question 5 → answered: yes, partial).
3. Empty-file lines: 23 & 41 empty in all years; 24 empty only 2022–2024.
4. Fahrplaene split: 61 PDF + 30 XLSX = 91 docs; filter `__MACOSX/` + `._*` junk.
5. Plan open question 2 (overlapping period files) → **answered: the multi-file
   line-years are complementary, not overlapping** — lines 5/34 (2022), 5 (2023),
   16 (2024), 5 (2024: Q1+Q2+H2), 16 (2025), 5 (2025) split their year into
   half-year (or Q1+Q2+H2) periods that partition `main_date_day` ranges. No
   cross-file dedup needed for these; `stop_event_id` is unique within each file
   (verified 314,405/314,405 on 2024 line-5 Q1).

---

## 3.1 `full_api_data/` — APC/AVL stop events (detail + examples)

Naming: `data_<start>_<end>_line_<n>.parquet`. Period granularity: mostly full-year;
half-year pairs (2022: lines 5, 34 · 2023/2025: line 5 · 2024/2025: line 16) and one
quarter split (2024 line 5: Q1+Q2+H2); all 2026 files named full-year. Distinct period
strings measured: 2022-01-01_2022-06-30 (×2), 2022-01-01_2022-12-31 (×35),
2022-07-01_2022-12-31 (×2), 2023 half/full, 2024 Q1/H1/full/H2, 2025 half/full,
2026 full (×40).

Per-year (rows = non-empty files):

| Year | Files (non-empty) | Empty | Rows | Data range (`main_date_day`) |
|---|---|---|---|---|
| 2022 | 36 | 3 | 5,787,537 | 2022-01-01 → 2022-12-31 |
| 2023 | 36 | 3 | 4,907,775 | 2023-01-01 → 2023-12-31 |
| 2024 | 34 | 7 | 5,014,518 | 2024-01-01 → 2024-12-31 |
| 2025 | 35 | 7 | 4,954,950 | 2025-01-01 → 2025-12-31 |
| 2026 | 36 | 4 | 1,317,714 | 2026-01-01 → **2026-04-06** |
| **Total** | **177** | **24** | **21,982,494** | 2022-01-01 → 2026-04-06 |

Schema — 35 base columns (inferred; all `Nullable(...)`; without the skip setting the
2022–2025 files fail on null-typed `is_holiday`):

```
stop_event_id Int64 | report_date DateTime64(9) | journey Int64 | quality_factor Int64
departure_plan_journey DateTime64(9) | departure_journey DateTime64(9)
line Int64 | line_route Int64 | direction String | route Int64 | day_type String
stop_sequence Int64 | station_number Int64 | station_short String | station String
departure_hour_station DateTime64(9) | departure_plan_station DateTime64(9)
arrival_plan_door DateTime64(9) | departure_plan_door DateTime64(9)
arrival_plan_stop DateTime64(9) | departure_plan_stop DateTime64(9)
vehicle_station Int64 | vehicle_type String | cumsum_distance_plan Int64
cumsum_travel_time_actual Int64 | passenger_boarding Int64 | passenger_exiting Int64
passenger_change Int64 | occupancy_departure Int64 | vehicle_utilization Float64
passenger_boarding_measured Int64 | passenger_exiting_measured Int64
passenger_kilometer Float64 | main_date_day Date32 | weekday String
```

2026-only extra 7 columns: `is_holiday Bool`, `day_group Float64`, `time_shift Float64`,
`next_station String`, `next_station_short String`, `edge String`, `unique_journey String`.

**Real example row — 2022** (`data_2022-01-01_2022-12-31_line_1.parquet`, first rows,
columns in schema order):

```
stop_event_id=44479490  report_date=2022-01-02 00:00:00  journey=147166  quality_factor=0
departure_plan_journey=2022-01-02 22:28:00  departure_journey=2022-01-02 22:29:08
line=1  line_route=12  direction="A"  route=405  day_type="K7=8~872"  stop_sequence=1
station_number=230  station_short="KÖNI"  station="Königsberger Straße"
departure_hour_station=2022-01-02 22:28:00  departure_plan_station=2022-01-02 22:28:00
arrival_plan_door=2022-01-02 22:29:08  departure_plan_door=2022-01-02 22:29:08
arrival_plan_stop=2022-01-02 22:29:08  departure_plan_stop=2022-01-02 22:29:08
vehicle_station=264  vehicle_type="GTN"  cumsum_distance_plan=0  cumsum_travel_time_actual=0
passenger_boarding=0  passenger_exiting=0  passenger_change=0  occupancy_departure=0
vehicle_utilization=0  passenger_boarding_measured=0  passenger_exiting_measured=0
passenger_kilometer=0  main_date_day=2022-01-02  weekday="Sonntag"
```

**Real example row — 2026** (`data_2026-01-01_2026-12-31_line_1.parquet`); note the new
`day_type` format (`01-MD021` vs `K7=8~872` in 2022 — a second, semantic drift beyond
the column set) and NULL derived columns:

```
stop_event_id=142279327  report_date=2026-01-07 00:00:00  journey=42265  quality_factor=0
departure_plan_journey=2026-01-07 12:42:00  departure_journey=2026-01-07 12:36:08
line=1  line_route=51  direction="A"  route=589  day_type="01-MD021"  stop_sequence=1
station_number=1008  station_short="BHS"  station="BHS"
... vehicle_station=206  vehicle_type="GTE" ... main_date_day=2026-01-07  weekday="Mittwoch"
is_holiday=NULL  day_group=NULL  time_shift=NULL  next_station=NULL  next_station_short=NULL  edge=NULL  unique_journey=NULL
```

Field-value profiles measured:

- `direction` ∈ {`A`, `B`}; `vehicle_type` ∈ {`GTN`, `GTE`, `Unknown`} (trams; `GTN`/`GTE`
  = WVV GT-N/GT-E types, `Unknown` appears in 2026); `weekday` German (`Sonntag`…).
- `quality_factor` range 0–200 in the 2022 line-1 file (semantics still undocumented).
- `day_type` 2022: 48 distinct DIVA-style codes in one line-year, e.g. `K7=8~872`,
  `K1+1~010`, `K2,8~821`, `K6-1~060` — undocumented; decoding still open (plan OQ3).
- Whole-bucket aggregates: 50,055,155 total `passenger_boarding`, 50,203,502
  `passenger_exiting`, avg `occupancy_departure` 14.6 (max 642), 377 distinct
  `station` names, 319 distinct `station_number`, 97,847 distinct `journey`, 71
  distinct `vehicle_station`.
- Stop reference is a triple: `station_number` (int, e.g. 230), `station_short`
  (`KÖNI`), `station` (`Königsberger Straße`) — **no DHID, no coordinates** (the plan's
  crosswalk rationale).

---

## 3.2 `Additional Data/` — 10 context CSVs (detail + examples)

All comma-separated except `dataAllStreets.csv` (`;`). Keys contain a space →
`Additional%20Data` in URLs. Measured (rows = data rows, header excluded):

| File | Rows | Columns (inferred types) | Range | Delimiter |
|---|---|---|---|---|
| `bavarian_public_holidays.csv` | 128 | `date Date, name String, regionalScope String, temporalScope String, nationwide Int64, subdivisions String` | 2019-01-01 → 2026-12-26 | `,` |
| `bavarian_public_holidays_daily.csv` | 2,922 | `date Date, public_holiday Int64, nationwide Int64` | 2019-01-01 → 2026-12-31 | `,` |
| `bavarian_school_holidays.csv` | 57 | `name String, startDate Date, endDate Date, type String, subdivisions String` | 2019-01-01 → **2027-01-08** | `,` |
| `bavarian_school_holidays_daily.csv` | 2,922 | `date Date, school_holiday Int64` | 2019-01-01 → 2026-12-31 | `,` |
| `events.csv` | 960 | `name String, start DateTime, end DateTime, concert Int64` | 2019-03-03 12:00 → 2025-12-23 20:30 | `,` |
| `events_daily.csv` | 70,105 | `date DateTime, event Int64, concert Int64` | 2019-01-01 00:00 → **2026-12-31** 00:00 (hourly expansion, incl. dates beyond `events.csv`) | `,` |
| `lectures.csv` | 30 | `start Date, end Date, jmu Int64, thws Int64` | 2018-10-01 → 2026-02-06 | `,` |
| `lectures_daily.csv` | 2,616 | `date Date, lecture_period_jmu Int64` (THWS not expanded) | 2019-01-01 → 2026-02-28 | `,` |
| `verkaufsoffene_sonntage.csv` | 12 | `date Date, name String, description String` | 2024-04-07 → 2026-11-29 | `,` |
| `dataAllStreets.csv` | 83,838 | 31 cols: `id, streetname, city, date, hour, timezone, weekday, pedestrians_count, towards_citycenter_…, awayfrom_citycenter_…, adult_/child_…, temperature, weather_condition, incidents, collection_type, …, zone_1..3_…` | 2019-04-02 → 2024-09-29 | **`;`** |

Sample rows (verbatim):

```csv
# bavarian_public_holidays.csv
2019-01-01,Neujahrstag,Regional,FullDay,1,\N
2019-01-06,Heilige Drei Könige,Regional,FullDay,0,\N

# bavarian_school_holidays.csv
Weihnachtsferien,2019-01-01,2019-01-04,school,BY

# events.csv
Faschingszug,2019-03-03 12:00:00,2019-03-03 23:59:59,0

# lectures.csv  (jmu = Julius-Maximilians-Universität, thws = THWS)
2018-10-01,2019-01-25,0,1
2018-10-15,2019-02-09,1,0

# verkaufsoffene_sonntage.csv
2024-04-07,Frühlingssonntag,Verkaufsoffener Sonntag Innenstadt

# dataAllStreets.csv (semicolon-delimited; note leading space in city, +0200 tz)
Schoenbornstrasse_2019-04-02_18;Schoenbornstrasse; Wuerzburg;2019-04-02;18;+0200;Tuesday;1324;682;642;1297;27;18;partly-cloudy-day;no_incident;measured;666;631;16;11;0;0;0;0.0;0.0;0.0;1324;682;642
```

`dataAllStreets.csv` detail: 3 streets — Schoenbornstrasse (48,174 rows, from
2019-04-02), Kaiserstrasse (17,568, from 2022-09-29), Spiegelstrasse (18,096, from
2022-09-07), all ending 2024-09-29; hourly grain; `timezone` ∈ {`+0100`, `+0200`}
(DST); `collection_type` = `measured`; includes weather (`temperature`,
`weather_condition`) and direction/zone splits — relevant as an ML context feature and
as evidence that the city already runs open sensor data (§5 references).

Interval→daily pairs are inconsistent as the plan says: `events_daily` is **hourly**
(and extends to 2026-12-31 while `events.csv` ends 2025-12-23), `lectures_daily` covers
JMU only, `bavarian_public_holidays_daily` carries an extra `nationwide` column. Load the
**interval** tables and expand calendars in SQL (plan §5.1) — confirmed as the right call.

---

## 3.3 `Fahrplaene/` — timetable documents (detail + examples)

25 line folders: `1-2-3-4-5, 6, 8, 10, 12, 13, 16, 20, 21, 26, 27, 28, 29, 33, 34, 91, 92, 93, 94, 95, 96, 97, 98, 99, 214`.
Note: parquet line numbers 7, 9, 23–25, 35, 41, 44, 53–55 have **no** folder — PDFs exist
only for the 25 listed lines (the WVV web selector also lists line 114, absent here).

91 real documents: **61 PDF + 30 XLSX**, ≈193 MiB total. XLSX workbooks are ~3.9–5.2 MB
each ("BMK …" files), PDFs 0.2–11.9 MB. Filenames carry validity dates
(`… ab 14.09.2021.pdf`, `… ab 03.06.2024.xlsx`, `Baustellenfahrplan_2023_Gesamt.pdf`,
`Komplett BMK SEV Grombühl ab 29.07.2024.pdf`, …) — the plan's "validity in filename"
premise holds; cover text additionally carries `Gültig ab:` / `Stand:` (parsed in the
archived test run, see `docs/archive/fahrplaene_extraction.md`).

Example filenames (verbatim keys):

```
wvv/Fahrplaene/1-2-3-4-5/Linie 1-5 ab 14.09.2021.pdf                    1,010,208 B
wvv/Fahrplaene/1-2-3-4-5/Baustellenfahrplan_2023_Gesamt.pdf             11,856,063 B
wvv/Fahrplaene/1-2-3-4-5/Komplett BMK SEV Grombühl ab 29.07.2024.pdf     1,823,188 B
wvv/Fahrplaene/1-2-3-4-5/BMK-Linie 5 ab 07.03.2022.xlsx                   4,304,326 B
wvv/Fahrplaene/8/Linie_08_web ab 03.06.2025.pdf                             491,774 B
wvv/Fahrplaene/13/BMK Linie 13 ab 16.09.2025Neu.xlsx                     4,421,660 B
wvv/Fahrplaene/34/Linie 34 ab 12.12.2022.pdf                             8,060,015 B
```

**PDF format example** — text-based (not scanned); `pdftotext -layout` excerpt of
`Baustellenfahrplan_2022_webversion.pdf` page 1 (full texts of the 1-2-3-4-5 folder are in
the gitignored `data/fahrplaene_text/`):

```text
            Baustellen-Fahrplan
            4 / 5 / SEV
                         Gültig ab: 30.07.2022

  Linie 4        Sanderau - Zellerau
                 Zellerau - Sanderau

 Linie 5 /       Rottenbauer - Heuchelhof - Heidingsfeld -
 SEV             Hauptbahnhof - Grombühl / Uni-Kliniken
 ...
```

Grid pages are stop-rows × trip-columns of `HH:MM` cells with annotations
(`ab`, `an`, `usw.`, `alle 15 min`, `bis …`); footnote legend rows like
`A = endet Hauptbahnhof/West`, `S = verkehrt nur an Schultagen`. Embedded fonts
partially lack `ToUnicode` maps (see `docs/archive/fahrplaene_pipeline_issues_and_fixes.md`)
— fine for the LLM path (page raster), relevant only to the retired parser.

**XLSX format example** — `BMK-Linie 5 ab 07.03.2022.xlsx` is a ZIP/OOXML workbook with
**one sheet** (`<sheet name="Linie 5" …/>`, used range `A1:DB718`, 717 rows × up to ~DB
columns): column A = stop names, columns C… = one trip per column, header rows carry
line/route and day type. `xl/sharedStrings.xml` (56 unique strings) contains exactly the
printed vocabulary:

```xml
<si><t>Rottenbauer</t></si><si><t>Andreas-Grieser-Straße</t></si>…
<si><t>Montags-freitags</t></si><si><t>Samstags</t></si><si><t>Sonn- und feiertags</t></si>
<si><t>an</t></si><si><t>ab</t></si><si><t>usw.</t></si><si><t>alle</t></si><si><t>bis</t></si>
<si><t>Grombühl - Hauptbahnhof - Heidingsfeld - Heuchelhof - Rottenbauer</t></si>
```

i.e. the XLSX are the Excel sources of the printed PDF timetables (same grid, plus
embedded network-map images `xl/media/image*.jpg`). They are out of the 2026 extraction
path (PDFs only) but are clean cross-check material — the grid is machine-readable here,
unlike in the PDFs.

---

## 4. GTFS source (DELFI archive) — status and references

`wvv/gtfs/` does not exist yet (plan §3.4 "to add" confirmed). The upstream archive was
re-checked live on 2026-11-18:

- Listing: `https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten (GTFS)/`
  → year folders `2020/` … `2025/` (**no `2026/` folder yet** as of 2026-11-18).
- `2025/` contains weekly Monday snapshots `YYYYMMDD_fahrplaene_gesamtdeutschland_gtfs.zip`,
  each ≈ 325–438 MB; newest = **`20251229_fahrplaene_gesamtdeutschland_gtfs.zip` (433 MB,
  2025-12-29)**. Same pattern in 2022–2024 folders.
- Plan open question 6 (how far the newest snapshot reaches into 2026): the inspected
  `20250106_…` sample had `feed_info` validity **2024-12-21 → 2025-06-14** (≈5.5-month
  lead). Extrapolating, `20251229` should be valid into ≈ **mid-2026** — verify exactly by
  downloading that one zip and reading `feed_info.txt` (`feed_start_date`/`feed_end_date`):
  ```bash
  curl -O "https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten%20(GTFS)/2025/20251229_fahrplaene_gesamtdeutschland_gtfs.zip"
  unzip -p 20251229_fahrplaene_gesamtdeutschland_gtfs.zip feed_info.txt
  ```
  Implication: 2026 schedule coverage from GTFS likely ends ~June 2026; the PDF path is
  needed for the rest of 2026 (matches plan §5.3).
- WVV filter verified earlier on the 2025-01-06 sample (plan §3.4): `agency_id = 13346`
  ("Würzburger Straßenbahn", Europe/Berlin), 96 routes incl. trams (route_type 0), buses
  (3), AST (700), SEV (`4 SEV`, `5 SEV`); stop space `de:09663:*` + `de:0967x:*`. 13 txt
  files, ≈6.5 GB unpacked, `stop_times.txt` 2.6 GB — filter before loading.
- GTFS example rows (from the plan §5.5, verified against the 2025-01-06 sample then;
  re-verify against any new snapshot):
  ```text
  # stops.txt — platform-level DHIDs, no parent_station
  "de:09663:40:0:01","","Wü Andreas-Grieser-Straße",,"49.767547","9.941197",0,,0,"",""
  # stop_times.txt — snapshot-local trip_id (unstable across exports)
  trip_id="de:nvm:stwü|Straba|1:_0_14", stop_sequence=4, stop_id="de:09663:40:0:01",
  arrival_time="07:14:00", departure_time="07:14:00"
  ```
  2023 snapshot used a different id style for line 1 (`5316210_0` vs `de:nvm:stwü|Straba|1:_0`
  in 2025) — the ID-instability premise for fingerprinting is real.

---

## 5. Provenance & external references for the term paper

| Data | Likely origin (verified reachable 2026-11-18) | Reference |
|---|---|---|
| APC/AVL parquet (`full_api_data/`) | WVV internal export ("full API data" of the DIVA-based APC/AVL system — `day_type` codes like `K7=8~872` are DIVA day types; `vehicle_type` GTN/GTE are WVV tram types). Not a public download; obtain provenance/license from the WVV data owner (plan phase 0 action item) | WVV B2B/ÖPNV pages: https://www.wvv.de/mobil-b2b/oepnv/ ; archived AVL/APC usage literature: TCRP Report 113 (Furth et al. 2006), https://www.trb.org/publications/tcrp/tcrp_rpt_113.pdf (see `docs/paper_sources/SOURCES_INDEX.md` S5.4) |
| Timetable PDFs/XLSX (`Fahrplaene/`) | WVV "PDF-Fahrpläne" page — https://www.wvv.de/mobil-b2c/pdf-fahrplan/ (line selector lists 1–10, 12, 13, 16, 20, 21, 23–29, 33–35, 41, 91–99, 114, 214; bucket has 25 of these as folders) | same URL; city page: https://www.wuerzburg.de/themen/verkehr--mobilitaet/fahrplanauskunft |
| GTFS snapshots | DELFI "deutschlandweite Sollfahrplandaten (GTFS)" archive | archive listing https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten%20(GTFS)/ (year folders, weekly zips); portal https://www.opendata-oepnv.de/ (Organisation → DELFI); GovData entry https://data.gov.de/suche/daten/delfi-timetable-gtfs . **License: check on the dataset page before publishing derived data** (DELFI feeds are commonly under Datenlizenz Deutschland / CC BY — verify) |
| Pedestrian counters (`dataAllStreets.csv`) | City of Würzburg open data portal (Huwise/ODS): https://opendata.wuerzburg.de/ — matching dataset `passantenzaehlung-uebersicht-csv` ("Passantenzählung Übersicht csv", daily aggregates for Kaiserstraße etc. with the same `pedestrians_count`/`weather_condition`/`zone_*`/temperature fields; the bucket CSV is the hourly, 3-street raw export of the same sensor system incl. Schoenbornstrasse & Spiegelstrasse). API: `https://opendata.wuerzburg.de/api/explore/v2.1/catalog/datasets/passantenzaehlung-uebersicht-csv/records?limit=5` ; Smart-City context: https://www.stadt-land-wue.de/smarte-region-wuerzburg . License per portal terms (verify; Würzburg ODP typically CC BY 4.0 / dl-de/by-2.0) | as left |
| Events (`events.csv`) | City event calendar: https://www.wuerzburg.de/events-termine (names match: Kiliani-Volksfest, Frühjahrsvolksfest, …) | as left |
| Lectures (`lectures.csv`, jmu/thws) | Semester/lecture periods of JMU Würzburg (https://www.uni-wuerzburg.de) and THWS (https://www.thws.de) — scraped interval table | as left |
| Holidays (`bavarian_*_holidays*.csv`) | Column schemas match public German holiday APIs — `date,name,regionalScope,temporalScope,nationwide,subdivisions` and `name,startDate,endDate,type,subdivisions` are OpenHolidays-API / schulferien-API-style exports for subdivision `BY`. Confirm the exact export used with whoever produced the CSVs | e.g. https://openholidaysapi.org/ , https://www.schulferien-api.de/ (both unreachable from this sandbox — verify from your machine) |
| Stop IDs / DHID | VDV Schrift 432 (DHID `de:<AGS>:…`), DELFI ZHV doc | https://www.vdv.de/downloads/3855/432SDS/forced ; https://www.delfi.de/media/zhv-erklaerdokument_04.09.2025_final.pdf (SOURCES_INDEX S2.17) |
| GTFS / GTFS-RT specs | MobilityData reference | https://gtfs.org/documentation/schedule/reference/ , https://gtfs.org/documentation/realtime/proto/ (S2.1–S2.3) |
| Parquet format | Apache Parquet spec (self-describing schema — basis for the 35↔42 column drift analysis) | https://parquet.apache.org/docs/file-format/ (S3.9) |

Full curated source list with download instructions for offline writing:
`docs/paper_sources/SOURCES_INDEX.md` (tags [CORE]/[OPT], direct PDF links).

**Term-paper-relevant facts worth citing (all measured above):**

- Volume: 21.98M APC stop-event rows (2022–2026-04-06), 40 lines, 177 files / 1.36 GB
  parquet; ~50.1M boardings total — justifies columnar OLAP (paper §3) and corrects the
  "5.1M rows" figure currently in `paper_plan.md`.
- Schema drift is real and two-layered: **structural** (35 → 42 columns in 2026, with
  `is_holiday` stored as parquet `null` type in 2022–2025 which breaks ClickHouse schema
  inference — reproduced) and **semantic** (`day_type` code format changed
  `K7=8~872` → `01-MD021` in 2026) — good material for the "resilience to schema drift"
  requirement (paper §1/§4, cite Confluent schema-evolution classes S4.30).
- 24 empty 598-byte placeholder files — "line didn't run" vs export failure still open
  (plan OQ1), but 23/41 are empty in every year and 24 only 2022–2024.
- 2026 APC data stops at 2026-04-06 (partial export — decides incremental vs full reload,
  plan OQ5).
- Context data is deliberately shipped as intervals + inconsistent pre-expansions
  (hourly `events_daily` reaching 2026-12-31 vs `events.csv` ending 2025-12-23;
  `lectures_daily` JMU-only) → calendar expansion belongs in SQL (paper §4.4).
- `dataAllStreets.csv` carries DST-aware offsets (`+0100`/`+0200`) split from
  date/hour, and a leading space in `city` — small but real cleaning work; the parquet
  timestamps carry **no** timezone at all (plan OQ4 still open — street CSV suggests
  local Europe/Berlin).
- Bucket hygiene: 118 macOS `__MACOSX`/`._*` artifacts and a `.DS_Store` inside the
  "raw" bucket — a nice concrete example for the provenance/raw-zone discussion.
- Fahrplaene: 91 documents (61 PDF + 30 XLSX) across 25 line folders with validity
  dates in filenames; the XLSX are machine-readable single-sheet grids (A1:DB718) —
  supports the "PDFs for 2026, XLSX as cross-check" split and the LLM-with-contract
  argument (rule-based grid parsing fails across layouts; see S4.22 + archive doc).

---

## 6. Reproduction appendix

```bash
# 0) credentials (never commit): read from rustfs/.env
AK=$(grep RUSTFS_ACCESS_KEY rustfs/.env | cut -d= -f2)
SK=$(grep RUSTFS_SECRET_KEY rustfs/.env | cut -d= -f2)

# 1) full bucket listing with sizes, via ClickHouse HTTP (default:default works today)
curl -s "http://default:default@localhost:8123/" --data-binary \
 "SELECT _path, _size FROM s3('http://rustfs:9000/wvv/**','$AK','$SK','LineAsString','line String') GROUP BY 1,2 ORDER BY 1 FORMAT TSV"

# 2) per-year parquet row counts
curl -s "http://default:default@localhost:8123/" --data-binary \
 "SELECT substring(_file,6,4) yr, count(DISTINCT _file) files, sum(r) rows FROM
  (SELECT _file, count() r FROM s3('http://rustfs:9000/wvv/full_api_data/*.parquet','$AK','$SK','Parquet','stop_event_id Int64') GROUP BY 1)
  GROUP BY 1 ORDER BY 1"

# 3) schema of one 2022 and one 2026 file (skip-setting as URL param for 2022-2025)
curl -s "http://default:default@localhost:8123/?input_format_parquet_skip_columns_with_unsupported_types_in_schema_inference=1" \
  --data-binary "DESCRIBE TABLE s3('http://rustfs:9000/wvv/full_api_data/data_2022-01-01_2022-12-31_line_1.parquet','$AK','$SK','Parquet')"
curl -s "http://default:default@localhost:8123/" --data-binary \
  "DESCRIBE TABLE s3('http://rustfs:9000/wvv/full_api_data/data_2026-01-01_2026-12-31_line_1.parquet','$AK','$SK','Parquet')"

# 4) CSV headers + samples
curl -s "http://default:default@localhost:8123/" --data-binary \
 "DESCRIBE TABLE s3('http://rustfs:9000/wvv/Additional%20Data/dataAllStreets.csv','$AK','$SK','CSVWithNames')"
curl -s "http://default:default@localhost:8123/?format_csv_delimiter=%3B" --data-binary \
 "SELECT * FROM s3('http://rustfs:9000/wvv/Additional%20Data/dataAllStreets.csv','$AK','$SK','CSVWithNames') LIMIT 2"

# 5) DELFI archive: newest snapshot + feed validity
curl -s "https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten%20(GTFS)/2025/"        # listing
curl -O "https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten%20(GTFS)/2025/20251229_fahrplaene_gesamtdeutschland_gtfs.zip"
unzip -p 20251229_fahrplaene_gesamtdeutschland_gtfs.zip feed_info.txt

# 6) Würzburg open data portal (pedestrian counters)
curl -s "https://opendata.wuerzburg.de/api/explore/v2.1/catalog/datasets/passantenzaehlung-uebersicht-csv/records?limit=3"
```

Notes: reading individual objects straight from the RustFS data volume does **not**
work (objects are erasure-coded dirs — `part.1` copies are truncated); use the S3 API
(e.g. a SigV4 presigned GET, or `s3()` from ClickHouse as above). Single-object reads
through `s3()` occasionally return transient 403s — retry.

---

## 7. Open questions — status after this discovery

From `data_pipeline_plan.md` §7:

1. Empty files meaning — **partially answered**: 23/41 empty in all 5 years; 24 empty
   2022–2024 only (has data 2025–2026); 2/7/9/25/35/99 scattered 2024–2026. Still need
   the data owner to say whether empty = "line didn't run".
2. Period-file overlap — **answered**: multi-file line-years are complementary halves/
   quarters, no duplicate `stop_event_id`s across them; no dedup needed (but keep
   `stop_event_id`-keyed idempotency for reloads).
3. `quality_factor` (0–200 observed), `passenger_*_measured` vs `passenger_*`,
   `day_type` codes (now two formats: `K7=8~872` pre-2026, `01-MD021` in 2026), units of
   `cumsum_*` — **still open**, ask WVV.
4. Parquet timezone — **still open**; street CSV proves the city publishes `+0100`/`+0200`
   explicitly, parquet carries nothing → assume Europe/Berlin, confirm.
5. 2026 partial — **answered**: data ends 2026-04-06, 1.32M rows → plan incremental
   reload for 2026.
6. DELFI snapshot reach into 2026 — **partially answered**: newest archive snapshot is
   `20251229` (no `2026/` folder as of 2026-11-18); expected validity ≈ mid-2026 based on
   the 2025-01-06 sample's 5.5-month lead; verify `feed_info.txt` of `20251229` (§6.5).
7. `full_api_data.line` ↔ GTFS `route_short_name` mapping — still open (needs phase 4).
8. DeepSeek practicalities — still open.
