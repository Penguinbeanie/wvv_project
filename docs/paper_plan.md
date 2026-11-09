# CONCEPT PAPER — DATA ENGINEERING & INFRASTRUCTURE
Smart Mobility Würzburg (Master Project Seminar WS 2026/27)

## THESIS
All WVV mobility data (APC/AVL stop events 2022–2026, schedules, context
calendars, optional real-time feeds) can be landed as clean, joinable,
versioned tables by combining three established patterns: a lakehouse-style
raw zone (S3 object storage as single source of truth), the medallion
convention (bronze/silver/gold), and a columnar OLAP engine (ClickHouse).
The one non-standard element — LLM-based extraction of 2026 timetable PDFs —
is contained by a strict validation contract and loads into the same model
as GTFS data, so all schedule sources converge on one gold layer keyed by
content fingerprints.

### 1. PROBLEM & SCOPE
Two downstream consumers with fixed interface needs: traffic simulation
(Domain 2) and ML capacity planning (Domain 3). Both need row-per-day,
row-per-trip data joined on stable keys (stop DHID, line, calendar date).
Not solved: no unified store exists for Ist-Daten (Parquet, 40 lines, 5.1M
rows), Soll-Daten (GTFS snapshots 2022–2025 + PDF timetables 2026), context
data (holidays, events, lectures, pedestrian counters), and — later, if
desired — daily real-time ingestion via official APIs.

### 2. REQUIREMENTS
Functional: unified stop events; schedules valid per concrete calendar day;
joinable context dimensions; optional incremental path for real-time/scheduled
API ingestion (added later without redesign). Non-functional: reproducibility
(every product recomputable from raw bucket), provenance (source_file +
loaded_at per table), idempotent reloads, append-only history (no
UPDATE/DELETE), schema-drift handling (35 vs. 42 columns across file vintages).

### 3. DATA SOURCES (claim: GTFS-first, documents and APIs only where the feed cannot go)
- a) DELFI GTFS weekly snapshots — authoritative, standardized, validated against printed Baustellenfahrplan 2023: 100% trip-level agreement.
- b) full_api_data Parquet — APC/AVL stop events (primary observed facts).
- c) Fahrplan PDFs 2026 — only for the year the feed does not cover.
- d) Context CSVs — loaded as interval tables, expanded in SQL.
- e) Real-time/operational APIs (optional, phase-in later): GTFS-RT (gtfs.de national stream, operator participation to verify) or WVV/regional APIs (DEFAS Bavaria / OpenData ÖPNV offer VDV 453 / EFA / TRIAS-style interfaces). Rationale: no single standard yet covers WVV real time, so ingestion is adapter-based behind one internal interface.

### 4. DESIGN DECISIONS (each as: alternative -> criterion -> decision)
- a) Raw storage: filesystem vs. S3-compatible object store -> heterogeneous formats, auditability, engine-agnostic access -> RustFS (S3 API).
- b) Engine: PostGIS vs. document store vs. columnar OLAP -> workload is analytical scans + ML exports, not spatial transactions (only stop coordinates, no routing) -> ClickHouse.
- c) Layering: single unlayered schema vs. layered zones -> reproducible reprocessing stages and auditable lineage -> raw/clean/dim for bucket loads plus bronze/silver/gold for schedules (medallion convention, stated as convention, not an engine feature).
- d) Cross-snapshot identity: raw GTFS IDs vs. content fingerprints -> GTFS IDs (route_id/trip_id/service_id) are re-invented on every export -> content fingerprints (cityHash64 of line/direction/stops/times) at (fingerprint, service_date) grain; silver = lossless evidence, gold = effective truth via argMax(snapshot_date); snapshot_count as confidence measure, was_corrected flags revisions.
- e) Gold granularity: compact validity ranges vs. exploded daily grain -> daily fact rows are the native input format for simulation and ML, and calendar resolution is precomputed once -> daily grain in gold_trip_day; storage duplication acknowledged, compensated by the range view (v_timetable_range).
- f) 2026 schedules: rule-based parsing vs. LLM extraction -> rule-based parsing failed as brittle across ~65 document layouts -> LLM extraction under a hard validation contract (time format, stop resolution against the GTFS stop list, monotone sequences, day_type enum), deterministic CSV conversion, nothing loaded unvalidated, reject/review queue; loads as a pseudo-snapshot (source='pdf').
- g) Processing paradigm: streaming vs. batch (Lambda/Kappa as the evaluated alternatives) -> current volume (~1.1M rows/yr APC, weekly snapshots) does not justify a streaming stack -> batch for historical backfill; any incremental ingestion added later is micro-batch (scheduled polling), not streaming.
- h) Orchestration: manual scripts vs. cron vs. workflow engine -> retry semantics, schedules, observability and an explicit pipeline topology; among engines, maturity/team familiarity -> Apache Airflow DAGs for all Python ingest jobs (GTFS snapshots, LLM extraction, later API adapters); Dagster/Prefect noted as the compared alternatives.
- i) Real-time API ingestion (future path, designed now): one adapter per source (GTFS-RT protobuf; WVV/EFA/TRIAS JSON) behind one internal interface, vs. a single consumer -> no single real-time standard covers WVV -> adapter-based ingestion: each run lands raw immutable payloads in the bucket (wvv/realtime/<date>/), a decode step writes bronze_rt_*, incremental merges update gold. GTFS-RT references the *feed's* trip_id, which is export-unstable; joining RT events to the fingerprint-keyed gold layer therefore goes through a per-snapshot trip_id->fingerprint lookup built from bronze_trips. Daily granularity suffices for simulation calibration; polling frequency is a config parameter, not a redesign.

### 5. VALIDATION
Trip-per-trip GTFS vs. printed timetable (done, 100%); row-count
reconciliation per line/year; schema/null profiling; acceptance check: every
APC journey finds a scheduled counterpart in the applicable timetable;
RT adapter sanity checks (feed freshness, trip_id resolution rate).

### 6. API CONTRACT
Provide: stop events (by line/date/journey), schedules at day grain, stop
and line dimensions, calendar flags; later: real-time observations if
ingested. Consume from domains 2/3: their feature requirements. Keys: DHID
stop IDs, GTFS route_short_name, calendar dates, content fingerprints.

### 7. CONTRIBUTIONS & LIMITATIONS
Contribution: a transferable pattern for (i) identity-stable versioning of
GTFS snapshots, (ii) validated LLM extraction integrated into a
conventional medallion stack, (iii) adapter-based API ingestion designed
for heterogeneous German PT real-time standards. Limitations: undocumented
APC semantics (quality_factor, *_measured), source timezone of Parquets
unconfirmed, fingerprint identity drifts across time corrections
(mitigated, not solved), 2026 APC coverage possibly partial, WVV
availability in national GTFS-RT streams unverified.

SOURCES TO CONSULT (per position)
- Lakehouse/raw-zone pattern: Armbrust et al., "Lakehouse", CIDR 2021.
- Medallion convention: Databricks docs (databricks.com; practitioner
  literature — state it as such, note the lack of academic treatment).
- Columnar OLAP justification: Stonebraker et al., C-Store, VLDB 2005;
  ClickHouse docs (clickhouse.com/docs) for MergeTree semantics.
- PostGIS counterpoint: postgis.net; PT data standards: Transmodel
  EN 12896 (transmodel.org), GTFS Reference (gtfs.org / MobilityData),
  GTFS-RT Reference (gtfs.org/realtime), SIRI EN 15531 and TRIAS (VDV),
  VDV 453; German feeds: archiv.opendata-oepnv.de (DELFI), gtfs.de
  (national GTFS/GTFS-RT stream, CC BY-SA 4.0), bayerninfo.de (DEFAS
  Bavaria real-time formats), vdv.de.
- Dimensional modeling / append-only history: Kimball & Ross, The Data
  Warehouse Toolkit, 3rd ed., 2013.
- Fingerprinting as entity resolution: Fellegi & Sunter, JASA 1969;
  Christophides et al., "End-to-End Entity Resolution for Big Data",
  ACM Computing Surveys 2020 (verify venue).
- Batch vs. streaming vs. micro-batch: Marz & Warren, Big Data (Lambda,
  2015); Kreps, "Questioning the Lambda Architecture" (O'Reilly, 2014).
- Orchestration: Airflow docs (airflow.apache.org; practitioner standard,
  no significant academic treatment — note this explicitly); compare
  Dagster/Prefect docs for the alternatives section.
- LLM extraction: Xu et al., "LLMs for Generative Information Extraction:
  A Survey" (arxiv.org/abs/2312.17617); Lu et al., "Large Language Model for
  Table Processing: A Survey", Frontiers of Computer Science 2025
  (doi.org/10.1007/s11704-024-40763-6); Kasem et al. 2024, table detection
  survey. Check newest survey before submission.
- APC data quality: Transportation Research Record (journals.sagepub.com),
  search "automatic passenger counting validation".
- Reproducibility/provenance: Wilkinson et al., FAIR principles, Scientific
  Data 2016 (doi.org/10.1038/sdata.2016.18); data quality: Batini &
  Scannapieco, Data and Information Quality, 2016.
- S3 API as de-facto interface: AWS S3 docs; RustFS (rustfs.com) only as an
  implementation detail — argue the pattern, not the product.