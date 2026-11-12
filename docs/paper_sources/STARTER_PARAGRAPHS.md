# Starter Paragraphs — Smart Mobility Würzburg Term Paper (Domain 1)

**What this is:** One clear, citation-backed starter paragraph per subtopic of `docs/paper_plan.md`, plus outlines for the 5 planned visuals (3 tables + 2 diagrams). Treat this as your scaffolding for writing offline: the sources are already matched to each argument, and each section follows the *technology evaluation → WVV context → justified decision* flow required by the seminar.

**How to use offline:**
- Rewrite everything in your own words — use these paragraphs as a clear argumentation skeleton, not as final text.
- Inline citations use author-year style. Every cited work maps to an ID in `SOURCES_INDEX.md` (listed in `(sources: …)` after each paragraph).
- **[verify]** = confirm author list or year from the downloaded PDF/DOI page before submission.
- Web documentation is cited with access year (2026); add the URL + access date when finalizing the bibliography (all URLs are in `SOURCES_INDEX.md`).
- Headings name the `master_pjs.pdf` criterion each section covers so the rubric mapping stays clear.

---

## §1 Introduction & System Context

### §1.1 Motivation and role of Domain 1 *(criterion: role of Domain 1, spec-driven approach)*

Public transport planning and traffic simulation depend on combining three types of data that usually come from different systems: planned schedules (*Soll*), observed passenger counts (*Ist*), and external context such as holidays, events, and weather. Prior transit research shows that archiving and linking vehicle-location (AVL) and passenger-counter (APC) data makes schedule debugging, running-time analysis, and service planning possible once the data is validated at the trip level (Furth, Hemily, Muller & Strathman, 2006). Likewise, multi-agent transport simulators like MATSim need both a transit schedule and empirical demand observations as core inputs for calibration (Horni, Nagel & Axhausen, 2016). In the Smart Mobility Würzburg project, Domain 1 (WVV Data Engineering & Infrastructure) acts as the central data platform and interface owner for Domain 2 (SUMO/MATSim traffic simulation), Domain 3 (capacity planning & ML), and the shared dashboard. Following Dehghani's data-mesh principle—where each domain owns and publishes well-defined data products instead of ad-hoc file exports (Dehghani, 2019)—we define clear cross-domain contracts in §5 before building pipelines. *(sources: S5.4, S2.20c, S1.5)*

### §1.2 Core requirements *(functional + non-functional)*

The platform's functional requirements follow directly from its downstream users: a unified stop-event history, calendar-resolved daily schedules, joinable context features (school holidays, university lectures, events, pedestrian counters, and weather), and a design that can later absorb continuous real-time feeds. Its non-functional requirements ensure that every consumer can trust the data: *reproducibility* from untouched raw files, clear *provenance* for every derived row, *append-only* history without destructive overwrites, and *resilience to schema drift*. These map onto established data-engineering practices: the FAIR principles require raw data to remain findable, accessible, interoperable, and reusable (Wilkinson et al., 2016); Batini and Scannapieco's quality framework (2016) defines the dimensions (completeness, accuracy, timeliness, consistency) used to profile incoming WVV feeds; and the event-sourcing pattern treats append-only event logs as the auditable base for reconstructing past states (Azure Architecture Center, 2026). Schema changes are handled as controlled evolution using compatibility rules rather than breaking downstream queries silently (Confluent, 2026). As a result, immutable raw files remain our ground truth throughout the paper, and every cleaning step is additive and traceable. *(sources: S1.1, S1.3, S1.4, S4.30)*

> **Visual 1 — System Context Diagram (target: §1, ~0.3 p.)**  
> **Type:** Block/architecture diagram (`D1` at center feeding `D2`, `D3`, and `Dashboard`).  
> **Nodes to include:**
> - *Upstream sources (left):* DELFI GTFS snapshots (2022–2025), WVV 2026 PDFs, APC/AVL Parquet (`full_api_data`), Context CSVs (`Additional Data`), future live APIs (DEFAS/TRIAS/GTFS-RT), DWD weather (planned).
> - *Domain 1 Platform (center):* S3 Raw Zone (RustFS) → ETL / Airflow → ClickHouse (`Bronze → Silver → Gold`).
> - *Consumers (right):* Domain 2 (SUMO/MATSim: stops, lines, daily trips, APC dwell calibration), Domain 3 (ML/OR: `clean.stop_events`, matched Soll–Ist views, calendar/context features), Shared Dashboard (read-only KPI SQL views + scenario/forecast sink tables).

---

## §2 Mobility Data Sources & Exchange Standards

### §2.1 Static schedule standards: GTFS vs. NeTEx/Transmodel *(criterion: evaluate data sources and formats)*

Two static schedule standards dominate European public transit. GTFS is a flat, CSV-based format (`agency`, `routes`, `trips`, `stop_times`, `calendar`, `calendar_dates`) maintained by MobilityData and used as the de-facto standard by routing and simulation tools (MobilityData, 2026). Both of Domain 2's simulators support it directly: Eclipse SUMO includes a built-in GTFS importer (DLR, 2026), and MATSim provides GTFS-to-schedule converters (matsim-org, 2026). NeTEx, by contrast, is the XML serialization of the European Transmodel standard (EN 12896:2022) and uses deeply nested, versioned XML frames with explicit `DayType` structures (CEN, 2022; Transmodel-CEN, 2024). Both standards cover the same transit concepts—the EU-backed DATA4PT mapping confirms that all GTFS and GTFS-RT data can be represented in NeTEx (DATA4PT, 2024)—and EU Regulation 2017/1926 requires National Access Points to support NeTEx (European Union, 2017). The real difference is practical: flat GTFS-style rows are much easier to validate row by row (especially when extracting 2026 timetables from PDFs), whereas nested NeTEx XML adds parsing and validation overhead without adding information our project needs. We therefore use GTFS as our internal data-model anchor: upstream German archives (DELFI) already publish GTFS, downstream simulators consume it natively, and simple row-level contracts keep validation clean. *(sources: S2.1, S2.19, S2.20, S2.6, S2.8, S2.7, S2.13)*

### §2.2 Real-time and operational APIs: GTFS-RT vs. VDV/SIRI/TRIAS *(criterion: evaluate data sources and formats)*

Live transit data splits along similar lines. GTFS-Realtime is a lightweight Protobuf feed with three message types—`TripUpdates`, `VehiclePositions`, and `ServiceAlerts`—whose trip IDs point directly to a static GTFS feed (MobilityData, 2026). It is easy to consume, but only if an operator or hub publishes it. In Germany, operators typically exchange real-time operational data using VDV-Schrift 453 (and VDV 454 for connection protection) (VDV, 2018), while passenger-facing request/response APIs use TRIAS (VDV 431-2), a German profile based on the European SIRI standard (EN 15531) (VDV, 2019; SIRI-CEN, 2026). Regionally, these feeds are aggregated by platforms like DEFAS Bayern (Mobilitätsplattform Bayern, 2026) and listed on Germany's National Access Point, the Mobilithek (Mobilithek, 2026). Because regional operators do not expose one uniform live stream—protocols, access rules, and coverage differ—we treat real-time ingestion as a pluggable adapter (§4.6): raw payloads land unchanged in object storage, and normalization happens downstream. *(sources: S2.3, S2.10, S2.11, S2.12, S2.9, S2.18, S2.14)*

### §2.3 Assessment of the concrete WVV project sources *(criterion: evaluate data sources and formats)*

Evaluating the actual WVV dataset reveals three source groups with distinct quality issues:
- *Soll (planned schedules):* Weekly Germany-wide DELFI GTFS snapshots (2022–2025) from OpenData ÖPNV (OpenData ÖPNV, 2026; cf. gtfs.de, 2026). A trip-by-trip check against WVV's 2023 summer construction timetable—including replacement bus services (`SEV`)—showed a 100% match. However, DELFI regenerates `route_id` and `trip_id` on every export, violating GTFS ID-stability best practices (MobilityData, 2026; google/transit, PR #171). To cover the 2026 schedule gap, ~65 per-line WVV timetable PDFs must be extracted.
- *Ist (observed demand):* ~5.11M APC/AVL stop-event rows (2022–2026 across 40 lines) stored as 201 Parquet files. They show classic data-quality issues as described by Batini & Scannapieco (2016): 24 empty 598-byte placeholder files across all years, plus schema drift from 35 columns (2022–2025) to 42 columns (2026), including a `null`-typed `is_holiday` column in older files.
- *Context:* 10 CSV files covering Bavarian public/school holidays, university lecture periods, Würzburg events, and hourly pedestrian street counters (`dataAllStreets.csv`, semicolon-delimited with `+0200` timestamps), alongside planned historical weather features from the DWD Climate Data Center (DWD, 2026).

This diagnosis directly drives the snapshot versioning, schema-tolerant loading, and calendar-resolution design in §3–§5. *(sources: S2.15, S2.16, S2.2, S2.5, S1.3, S5.10)*

> **Visual 2 — Transit Standards Comparison Table (target: §2, ~0.35 p.)**  
> **Type:** Two-part comparison table (Static: `GTFS vs. NeTEx/Transmodel`; Real-Time: `GTFS-RT vs. VDV 453/454 vs. SIRI/TRIAS`).  
> **Suggested columns:** `Standard` | `Format / Transport` | `Strengths` | `Limitations` | `Role in WVV Platform`.  
> **Key rows:** GTFS (CSV, simulator-native, ID churn in DELFI → internal anchor), NeTEx (XML/XSD, rich `DayType`, EU Reg. 2017/1926 → too complex for PDF validation), GTFS-RT (Protobuf, lightweight, needs static ID match → Phase-2 adapter), VDV 453/454 & SIRI/TRIAS (XML/SOAP/HTTP, German/DEFAS native → raw landing via adapter).

---

## §3 Storage & Spatial Database Architectures

### §3.1 Workload analysis *(criterion: compare spatial database architectures)*

Before comparing database products, we have to separate two different workloads. Domain 2's simulators (SUMO/MATSim) perform *topological GIS workloads*—routing on road networks, map-matching, and polygon intersections—inside their own preprocessing tools. Domain 1 does not duplicate that work. Instead, Domain 1 runs an *analytical data platform workload*: scanning millions of time-series stop events (5.11M rows and growing), storing and comparing weekly schedule snapshots, joining `Ist × Soll × Calendar` at daily grain, and exporting bulk feature tables for ML and simulation. In Domain 1, spatial data consists mainly of fixed stop coordinates (`lat`, `lon`, `DHID`). Database research clearly shows that read-heavy analytical scans and aggregations perform far better on column-oriented storage than on row-oriented engines, because columnar systems read only needed columns, compress repetitive values heavily, and process data in vectorized batches (Stonebraker et al., 2005; Abadi, Boncz, Harizopoulos, Idreos & Madden, 2013; Boncz, Zukowski & Nes, 2005). This workload split guides both the comparison in §3.2 and the domain boundary in §5. *(sources: S3.2, S3.4, S3.3)*

### §3.2 Comparative evaluation of storage paradigms *(criterion: compare spatial database architectures)*

Three storage paradigms are realistic candidates:
1. *Relational Spatial RDBMS (PostgreSQL + PostGIS):* Provides full OGC geometry types, GiST spatial indexes, and strict ACID transactions (PostGIS, 2026; PostgreSQL, 2026). It is the best option for interactive spatial editing or road-network queries, but its row-oriented layout carries extra I/O and CPU overhead on wide analytical scans and multi-snapshot deduplication (Stonebraker et al., 2005; Abadi et al., 2013).
2. *NoSQL Stores (Document / Wide-Column):* Document stores like MongoDB handle nested, changing JSON payloads well (MongoDB, 2026), and wide-column or key-value systems like Cassandra, Bigtable, and Dynamo scale write throughput by limiting query and consistency guarantees (Lakshman & Malik, 2010; Chang et al., 2006; DeCandia et al., 2007). However, NoSQL surveys note that ad-hoc multi-table joins and analytical aggregations are their main weakness (Davoudian, Chen & Liu, 2018)—and `Ist × Soll × Calendar` joins are core to Domain 1.
3. *Lakehouse Object Storage + Columnar OLAP:* Decouples cheap, immutable storage of open columnar files (Apache Parquet, 2026) on an S3-compatible object store (AWS, 2026; implemented locally with RustFS, 2026) from a fast analytical query engine (Armbrust, Ghodsi, Xin & Zaharia, 2021). *(sources: S3.7, S3.8, S3.2, S3.4, S3.10, S3.11, S3.12, S3.13, S3.14, S3.1, S3.9, S3.15, S3.16)*

### §3.3 Architectural synthesis: why S3 + ClickHouse for WVV *(decision)*

Matching our analytical workload against these options leads to **S3-compatible object storage (RustFS) + ClickHouse**. All raw files (Parquet, CSV, GTFS ZIPs, PDFs) live untouched in one S3 bucket as the reproducible source of truth, following the lakehouse principle of separating storage from compute (Armbrust et al., 2021). ClickHouse serves as the analytical engine: its `MergeTree` table family uses sorted, compressed columnar parts and sparse primary indexes designed for fast time-series scans and array columns (ideal for storing per-trip stop and departure vectors) (Schulze et al., 2024; ClickHouse, 2026). ClickHouse's `s3()` table function reads Parquet and CSV files straight from RustFS without extra ETL glue, while `ReplacingMergeTree` and `argMax` support append-only snapshot versioning without destructive `UPDATE` or `DELETE` operations (ClickHouse, 2026). We also draw a clear boundary: if Domain 1 ever had to take over OpenStreetMap road-graph processing or complex spatial routing for Domain 2, PostGIS with GiST indexing would be the right tool for that job (PostGIS, 2026)—as long as that stays in SUMO/MATSim, S3 + ClickHouse is the cleaner fit. *(sources: S3.5, S3.6, S3.9, S3.1, S3.7)*

> **Visual 3 — Storage & Spatial Database Decision Matrix (target: §3, ~0.3 p.)**  
> **Type:** Evaluation matrix comparing `PostgreSQL/PostGIS` vs. `NoSQL (MongoDB / Cassandra)` vs. `S3 + ClickHouse`.  
> **Suggested rows (criteria):** Spatial / GIS support (OGC, GiST) | Time-series scan & compression | Multi-table analytical joins (`Ist × Soll × Cal`) | Schema drift & raw file archiving | Append-only snapshot versioning | Fit for WVV Domain 1.  
> **Takeaway row:** PostGIS wins for topological GIS (stays in D2); NoSQL wins for high-write key-value/JSON; S3 + ClickHouse wins for D1's analytical, append-only workload.

---

## §4 ETL/ELT Pipeline & Continuous Processing

### §4.1 Processing paradigm and orchestration *(criterion: design robust ETL pipelines for continuous processing)*

The first pipeline choice is batch/micro-batch versus true streaming. The Lambda architecture combines a batch layer and a speed layer over immutable raw data (Marz & Warren, 2015), while Kreps's Kappa architecture argues that maintaining two separate codebases is costly and can be avoided by running everything through a log-based stream processor like Kafka (Kreps, 2014; Kreps, Narkhede & Rao, 2011). At WVV's scale—roughly 1.1M APC rows per year, weekly GTFS snapshots, and daily simulation or ML cycles—sub-second streaming latency brings no practical benefit, while tools like Kafka and Flink add heavy operational overhead. Scheduled batch and micro-batch jobs (polling APIs on a schedule) give us continuous updates with much simpler operations. For orchestration, we choose **Apache Airflow** over plain cron, Dagster, and Prefect (Apache Airflow, 2026; Dagster, 2026; Prefect, 2026). Airflow's explicit DAG dependencies, automatic retries, and built-in backfill semantics make it straightforward to reprocess multi-year GTFS snapshots and recover cleanly from failed loads. *(sources: S4.5, S4.6, S4.8, S4.10, S4.11, S4.12)*

### §4.2 Medallion layering over an immutable raw zone *(criterion: design robust ETL pipelines for continuous processing)*

Our pipeline organizes data using the Medallion pattern (Databricks, 2026): **Bronze** stores raw data 1:1 with provenance metadata (`source_file`, `loaded_at`, `snapshot_date`), **Silver** holds type-cast, schema-unified, append-only observations, and **Gold** exposes deduplicated business truth for consumers. Instead of duplicating files across Delta tables, we keep a single physical raw copy in the S3 bucket and materialize Bronze, Silver, and Gold as ClickHouse schemas—combining lakehouse reproducibility (Armbrust et al., 2021) with FAIR data preservation (Wilkinson et al., 2016). Retaining every historical observation in Silver follows Kimball's slowly-changing-dimension (SCD) practice: keeping superseded rows with validity timestamps lets us answer both "what is true now" and "what was published then" (Kimball & Ross, 2013). While critics note that Medallion architectures can multiply storage and compute (cf. §6.1), ClickHouse's columnar compression and single-source S3 landing zone keep that cost low. *(sources: S4.3, S3.1, S1.1, S4.1)*

### §4.3 Single-point calendar resolution *(design pattern)*

GTFS defines service schedules using weekday masks, date ranges (`calendar.txt`), and per-date exceptions (`calendar_dates.txt`), and uses operating-day times past midnight such as `24:03` (MobilityData, 2026). If every downstream ML script, simulation export, and dashboard query had to re-implement this calendar logic, bugs and inconsistencies would multiply—a classic warehouse anti-pattern (Kimball & Ross, 2013). Instead, our Silver layer expands `calendar` and `calendar_dates` once per snapshot into concrete `Europe/Berlin` service dates (`silver_service_dates`), and joins Bavarian public holidays, school holidays, university lecture periods, and event intervals into a single `ref_calendar` dimension. Downstream consumers simply join on `service_date` without touching GTFS exception rules, ensuring that school-day and holiday schedules match across all teams. *(sources: S2.1, S4.1)*

### §4.4 Cross-snapshot entity resolution: content fingerprinting *(design pattern)*

Because DELFI snapshots regenerate `route_id`, `trip_id`, and `service_id` on every weekly export (for example, line 1 changes from `5316210_0` in 2023 to `de:nvm:stwü|Straba|1:_0` in 2025), raw GTFS IDs cannot be used to track trips over time (§2.3), a known gap in the GTFS ecosystem (MobilityData, 2026; google/transit, PR #171). Entity resolution literature describes this as matching records via quasi-identifiers and then consolidating them into a single truth (Christophides, Efthymiou & Stefanidis, 2020). Rather than using probabilistic record linkage (Fellegi & Sunter, 1969), which adds uncertainty and tuning overhead, we compute a deterministic **content fingerprint** (`cityHash64` over line, normalized terminus/direction, stop-ID sequence, and arrival/departure minute arrays). Silver keeps every `(snapshot_date, fingerprint, service_date)` observation, while Gold resolves the latest truth via `argMax(..., snapshot_date)` (ClickHouse, 2026). This automatically yields a `snapshot_count` confidence score and a `was_corrected` flag when a schedule changes mid-period (Batini & Scannapieco, 2016). While minute-level retimings create a new fingerprint (§6.1), building stable identity on top of unstable GTFS exports aligns with recent transit-schedule research [verify authors] (2026). *(sources: S2.2, S2.5, S4.15, S4.16, S3.6, S1.3, S4.17)*

### §4.5 2026 PDF extraction with a deterministic validation contract *(design pattern)*

Since DELFI snapshots do not cover all of 2026, the 2026 timetable must be extracted from ~65 heterogeneous WVV PDFs. In an earlier test run on 9 PDFs (lines 1–5), coordinate-based grid parsing with PyMuPDF worked only after adding ~14 fragile layout heuristics (page-block splitting, `usw.` cadence gap-filling, headerless reverse-grid flipping, and de-spacing mangled dates), and still struggled with SEV labels and missing font encodings—consistent with research showing that layout diversity makes rule-based table recognition brittle [verify authors] (arXiv 2211.08469). Multimodal LLMs can extract structured tables zero-shot across varied layouts (Wei et al., 2023; Xu et al., 2024; Lu et al., 2025), but because LLMs can hallucinate [verify authors] (arXiv 2311.05232; arXiv 2404.18930), raw model output can never be trusted directly. We therefore wrap LLM extraction (using PyMuPDF text + page images) in a **deterministic validation contract** inspired by JSON Schema and declarative expectation checks (JSON Schema, 2026; Great Expectations, 2026): every extracted trip must have ≥2 stops, valid `HH:MM` or `>24:00` times, non-decreasing stop times, known DHID stops, and valid day-type/footnote codes. Failing rows go to a manual review queue; passing rows enter the exact same Bronze → Silver → Gold pipeline as a `source='pdf'` pseudo-snapshot. *(sources: S4.22, S4.23, S4.19, S4.20, S4.26, S4.27, S4.29)*

### §4.6 Continuous real-time extension *(design pattern)*

To support live data without redesigning the lakehouse, an ingestion adapter polls regional operational feeds (GTFS-RT or TRIAS/SIRI via DEFAS, cf. §2.2) on a schedule and writes raw payloads unchanged into S3, keeping full replayability (Armbrust et al., 2021). Because live feeds use either GTFS-RT `trip_id`s or German operator keys (MobilityData, 2026; VDV, 2018) that do not match our historical fingerprints directly, the adapter joins incoming trips to Gold **fingerprints** via per-snapshot lookup tables built in §4.4. Recent work on correcting published timetables from real-time feeds [verify authors] (rt2gtfs, 2026) shows how this alignment enables Phase-2 feedback loops where observed travel times refine planned schedules. *(sources: S4.18, S3.1, S2.3, S2.10, S3.6)*

> **Visual 4 — End-to-End Medallion & Fingerprinting Flow Diagram (target: §4, ~0.4 p.)**  
> **Type:** Pipeline flow diagram (left-to-right across 4 stages).  
> **Flow to show:**
> 1. *Raw Zone (RustFS S3):* `gtfs/*.zip` + `Fahrplaene/*.pdf` (via PyMuPDF + LLM + Validation Contract gate → `curated/*.csv`) + `full_api_data/*.parquet` + `Additional Data/*.csv` + future live adapter.
> 2. *Bronze (ClickHouse):* `bronze_*` tables 1:1 with source + `snapshot_date` / `source_file` / `loaded_at`.
> 3. *Silver (ClickHouse):* `silver_service_dates` (single-point calendar expansion), `silver_trip` (computes `fingerprint = cityHash64(line, direction/terminus, stop_ids, arr/dep_minutes)`), `silver_trip_day` (lossless observation log), `clean.stop_events` (unified 42-col schema).
> 4. *Gold (ClickHouse):* `gold_trip_day` (`argMax(..., snapshot_date)` → `snapshot_count`, `was_corrected`), `gold_stop`, `gold_line`, `ref_calendar` → feeds D2, D3, Dashboard.

---

## §5 Cross-Domain Data & API Contract

### §5.1 Ubiquitous join keys *(criterion: define the API contract)*

A reliable cross-domain contract depends on shared join keys that every team uses:
- **Spatial / Stop Key:** The official German stop ID (`DHID`), defined in VDV-Schrift 432 and distributed via DELFI's ZHV register (VDV, 2016; DELFI, 2025)—primarily `de:09663:*` for Würzburg plus `de:0967x:` where WVV lines cross into surrounding municipalities. It links GTFS stops, LLM-extracted PDF stops, APC stations, and simulation nodes.
- **Network Key:** Stable GTFS `route_short_name` (including `SEV` replacement lines) paired with a normalized terminus/direction.
- **Temporal Key:** ISO `service_date` in `Europe/Berlin`, aligned with GTFS operating-day rules including times past `24:00` (MobilityData, 2026).
- **Trip Key:** The deterministic content `fingerprint` from §4.4, which stays stable across DELFI exports and 2026 PDFs.

Declaring these four keys as the platform's public interface ensures domains integrate via stable data contracts rather than brittle shared code (Dehghani, 2019). *(sources: S2.17, S2.1, S1.5)*

### §5.2 What Domain 1 provides — outputs and access patterns *(criterion: deliverables)*

Domain 1 tailors its deliverables to each consumer:
- **To Domain 2 (SUMO/MATSim):** Versioned stop coordinates (`gold_stop`), line metadata (`gold_line` with `route_type` for tram/bus/AST/SEV), daily trip schedules with `arr_minutes` and `dep_minutes` arrays in GTFS-compatible views (DLR, 2026; matsim-org, 2026), and empirical APC boarding/dwell distributions for calibration (Furth et al., 2006).
- **To Domain 3 (Capacity Planning & ML):** Schema-unified `clean.stop_events` (2022–2026), matched `Soll–Ist` trip views for delay and load modeling, and pre-joined calendar, holiday, lecture, event, and pedestrian-counter feature tables (with DWD historical weather planned as an external join, 2026).
- **To the Shared Dashboard:** Fast analytical SQL views for KPIs (line utilization, punctuality, schedule coverage) plus sink tables to store simulation results and ML forecasts.

Access uses two simple interfaces: read-only SQL views over ClickHouse's HTTP interface for interactive queries and dashboards (ClickHouse, 2026), and versioned Parquet/CSV exports in S3 for reproducible ML training and simulation runs (Apache Parquet, 2026; Armbrust et al., 2021). *(sources: S2.19, S2.20, S5.4, S5.10, S5.2, S3.9, S3.1)*

### §5.3 What Domain 1 needs — inputs and open questions *(criterion: needs)*

Because the interface is two-way, Domain 1 also specifies what it needs from partners and stakeholders:
- **From Domain 2:** Confirmation on whether GTFS `shapes.txt` geometries or custom OSM stop-to-link mappings must be stored in D1 (which determines the PostGIS boundary from §3.3), plus output schemas for simulation sink tables.
- **From Domain 3:** Preferred temporal/spatial aggregation grain, any additional external features—such as DWD historical weather (DWD, 2026), given documented weather and calendar effects on transit ridership [verify authors] (Pierce County bus study; extreme-weather study; calendar-events study)—and the write-back schema for optimized schedules (keyed by `fingerprint` and `service_date`).
- **From WVV Stakeholders:** Clear documentation of undocumented APC fields (`quality_factor`, `passenger_*_measured` vs. `passenger_*`, raw Parquet timezone), since APC research shows counter data is only reliable after quality filtering (Kimpel et al. [verify year]; Furth et al., 2006), plus access details for live feeds via DEFAS (§2.2). *(sources: S5.10, S5.11, S5.12, S5.6, S5.4, S2.18)*

> **Visual 5 — Bidirectional Cross-Domain Contract Table (target: §5, ~0.4 p.)**  
> **Type:** Two-part interface table (`D1 Provides` and `D1 Needs`) with shared join keys listed in the table header/footer (`DHID`, `route_short_name`, `service_date`, `fingerprint`).  
> **Suggested columns:** `Partner` | `Direction` | `Data Product / Question` | `Format / Interface` | `Key / Grain`.  
> **Key rows:** D2 (Provides: `gold_stop`, `gold_line`, `gold_trip_day`, APC dwell stats via SQL/Parquet; Needs: `shapes.txt`/OSM requirement, sim output schema) | D3 (Provides: `clean.stop_events`, Soll–Ist views, calendar/context features via S3 Parquet/SQL; Needs: target grain, DWD weather spec, forecast write-back schema) | Dashboard (Provides: KPI views, scenario/forecast sink tables via ClickHouse HTTP) | WVV (Needs: `quality_factor` & `*_measured` semantics, Parquet timezone, DEFAS live access).

---

## §6 Critical Discussion & Conclusion

### §6.1 Key architectural trade-offs

Three design trade-offs require an explicit defense:
1. *Daily exploded schedule grain vs. compact date ranges:* Expanding schedules into one row per `(fingerprint, service_date)` duplicates trip data across days, but ClickHouse's columnar compression keeps storage small while giving ML and simulation zero-cost date joins (Kimball & Ross, 2013; Abadi et al., 2013; Schulze et al., 2024).
2. *Content fingerprints vs. minor retimings:* Fingerprints solve weekly GTFS ID churn, yet even a one-minute schedule adjustment creates a new hash. We handle this through `argMax` revision tracking (`was_corrected`, `snapshot_count`) at the line and time-window level so small edits appear as traceable corrections—a practical solution to the stable-ID problem [verify authors] (2026).
3. *Medallion layering overhead:* Critics argue that Medallion layers duplicate data and compute, which we mitigate by keeping one raw copy in S3 and materializing layers inside a single columnar engine for auditability and reproducibility (Databricks, 2026; Wilkinson et al., 2016). *(sources: S4.1, S3.4, S3.5, S3.6, S4.17, S4.3, S1.1)*

### §6.2 Limitations and data risks

Four main data risks remain open for Phase 2:
1. *APC sensor semantics:* `quality_factor` and `passenger_*_measured` are undocumented vendor fields. Because APC accuracy studies show count errors of several percent even in validated European bus fleets (Kimpel et al. [verify year]; Furth et al., 2006; European APC studies [verify authors], 2019, 2025), Gold passenger aggregates must be treated cautiously until WVV confirms these flags.
2. *Incomplete Parquet exports:* 24 empty placeholder files appear across 2022–2026, and 2026 currently has only ~339k rows (vs. ~1.1M/year earlier), so pipelines must separate missing exports from zero-ridership days (Batini & Scannapieco, 2016).
3. *PDF footnote ambiguity:* Per-trip school-day footnotes that fail the validation contract drop into a manual review queue, as LLM hallucination risks make a human check mandatory [verify authors] (arXiv 2311.05232).
4. *Unconfirmed live coverage:* EU Regulation 2017/1926 mandates National Access Points (European Union, 2017), but actual WVV live-feed availability on DEFAS or Mobilithek is not yet verified.

Quality assurance is therefore built into every stage—contracts at ingestion (§4.5), provenance flags at resolution (§4.4), and explicit risk tracking here. *(sources: S5.6, S5.4, S5.8, S5.9, S1.3, S4.26, S2.13)*

### §6.3 Conclusion and Phase-2 outlook

This architecture unifies heterogeneous municipal mobility data without heavy GIS-transactional overhead by combining an immutable S3 raw zone, an append-only Medallion pipeline, and ClickHouse as a columnar OLAP engine. Where real-world feeds break standards—regenerated GTFS IDs and PDF-only 2026 timetables—content fingerprinting and contract-validated LLM extraction bridge the gap cleanly. Each building block rests on proven practice: FAIR raw preservation (Wilkinson et al., 2016), event-sourced/SCD append-only history (Azure Architecture Center, 2026; Kimball & Ross, 2013), decoupled lakehouse storage (Armbrust et al., 2021), and data-mesh domain contracts (Dehghani, 2019). For Phase 2, two extensions fit naturally onto this foundation: real-time correction loops where observed `Ist` data refines `Soll` truth (rt2gtfs [verify authors], 2026), and expanded ML feature tables adding external DWD weather. Resolving the open questions in §5.3 is the implementation team's first step, not architectural debt. *(sources: S1.1, S1.4, S4.1, S3.1, S1.5, S4.18)*

---

## Seed Reference List (map to SOURCES_INDEX.md IDs)

Entries marked **[verify]** need author/year confirmation from the downloaded PDF or DOI page. Web docs: append URL + access date (all in `SOURCES_INDEX.md`).

### Academic papers & books
- Armbrust, M., Ghodsi, A., Xin, R., & Zaharia, M. (2021). Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. *CIDR 2021*. [S3.1]
- Stonebraker, M., Abadi, D. J., Batkin, A., et al. (2005). C-Store: A column-oriented DBMS. *VLDB 2005*. [S3.2]
- Boncz, P., Zukowski, M., & Nes, N. (2005). MonetDB/X100: Hyper-pipelining query execution. *CIDR 2005*. [S3.3]
- Abadi, D., Boncz, P., Harizopoulos, S., Idreos, S., & Madden, S. (2013). The design and implementation of modern column-oriented database systems. *Foundations and Trends in Databases, 5*(3), 197–280. [S3.4]
- Schulze, R., et al. (2024). ClickHouse — Lightning fast analytics for everyone. *PVLDB, 17*(12), 3731–3744. [S3.5]
- Lakshman, A., & Malik, P. (2010). Cassandra: A decentralized structured storage system. *SIGOPS Operating Systems Review, 44*(2). [S3.11]
- Chang, F., Dean, J., Ghemawat, S., Hsieh, W. C., Wallach, D. A., Burrows, M., Chandra, T., Fikes, A., & Gruber, R. E. (2006). Bigtable: A distributed storage system for structured data. *OSDI '06*. [S3.12]
- DeCandia, G., et al. (2007). Dynamo: Amazon's highly available key-value store. *SOSP '07*. [S3.13]
- Davoudian, A., Chen, L., & Liu, M. (2018). A survey on NoSQL stores. *ACM Computing Surveys, 51*(2). [S3.14]
- Kreps, J. (2014). Questioning the Lambda Architecture. *O'Reilly Radar*. [S4.6]
- Kreps, J., Narkhede, K., & Rao, J. (2011). Kafka: A distributed messaging system for log processing. *NetDB '11*. [S4.8]
- Marz, N., & Warren, J. (2015). *Big Data: Principles and best practices of scalable realtime data systems*. Manning. [S4.5]
- Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit* (3rd ed.). Wiley. [S4.1]
- Christophides, V., Efthymiou, V., & Stefanidis, K. (2020). End-to-end entity resolution for big data: A survey. *ACM Computing Surveys, 53*(2). [S4.15]
- Fellegi, I. P., & Sunter, A. B. (1969). A theory for record linkage. *JASA, 64*(328), 1183–1210. [S4.16]
- Wilkinson, M. D., Dumontier, M., Aalbersberg, I., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. [S1.1]
- Batini, C., & Scannapieco, M. (2016). *Data and Information Quality: Dimensions, Principles and Techniques*. Springer. [S1.3]
- Xu, D., et al. (2024). Large language models for generative information extraction: A survey. arXiv:2312.17617. [S4.19]
- Lu, W., Zhang, J., Fan, J., et al. (2025). Large language model for table processing: A survey. *Frontiers of Computer Science* / arXiv:2402.05121. [S4.20]
- Wei, X., Cui, X., Cheng, N., et al. (2023). ChatIE: Zero-shot information extraction via chatting with ChatGPT. arXiv:2302.10205. [S4.23]
- Horni, A., Nagel, K., & Axhausen, K. W. (Eds.). (2016). *The Multi-Agent Transport Simulation MATSim*. Ubiquity Press. [S2.20c]
- Furth, P. G., Hemily, B., Muller, T. H. J., & Strathman, J. G. (2006). *Using Archived AVL-APC Data to Improve Transit Performance and Management* (TCRP Report 113). TRB. [S5.4]
- Dehghani, Z. (2019). How to move beyond a monolithic data lake to a distributed data mesh. martinfowler.com. [S1.5]
- Kimpel, T. J., et al. **[verify year/authors]**. Automatic passenger counter evaluation: Implications for National Transit Database reporting. *Transportation Research Record, 1835*. [S5.6]
- **[verify authors]** (2026). Recurring public transit schedules: Stable identification from GTFS and similarity analysis. arXiv:2606.14713. [S4.17]
- **[verify authors]** (2026). rt2gtfs: A scalable framework for correcting public transport timetables using real-time data. arXiv:2603.11477. [S4.18]
- **[verify authors]** Deep learning for table detection and structure recognition: A survey. arXiv:2211.08469. [S4.22]
- Tonmoy, S. M., et al. **[verify]** (2023). A survey on hallucination in large language models. arXiv:2311.05232. [S4.26]
- **[verify authors]** (2024). Hallucination of multimodal large language models: A survey. arXiv:2404.18930. [S4.26]
- **[verify authors]** Empirical study on the accuracy and precision of automatic passenger counting in European bus services. *Open Transportation Journal, 13*. [S5.8]
- **[verify authors]** (2025). Accuracy of automatic passenger counting in open mass transit systems. *Open Transportation Journal, 19*. [S5.9]
- **[verify authors]** (2024). Large language models (LLMs) on tabular data: A survey. arXiv:2402.17944. [S4.21]
- **[verify authors]** Impact of weather on bus ridership in Pierce County. *Journal of Public Transportation*. [S5.11]
- **[verify authors]** (2025). Predictors of sustainable student mobility in a suburban setting. *Sustainability, 17*(15), 6726. [S5.13]

### Standards, regulations & datasets
- MobilityData. (2026). *GTFS Schedule Reference; GTFS Schedule Best Practices; GTFS Realtime Proto Reference*. gtfs.org. [S2.1, S2.2, S2.3]
- google/transit. *Pull Request #171: Define and require "ID stability"*. [S2.5]
- CEN. (2022). *Transmodel — Reference data model for public transport (EN 12896:2022 series)*. [S2.8]
- TransmodelEcosystem / SIRI-CEN. (2026). *NeTEx (CEN/TS 16614 series)* and *SIRI (EN 15531)* — official GitHub schema repositories. [S2.6, S2.9]
- DATA4PT. (2024). *Outline comparison and mapping between NeTEx & GTFS*. [S2.7]
- European Union. (2017). *Commission Delegated Regulation (EU) 2017/1926*. EUR-Lex. [S2.13]
- VDV. (2016). *VDV-Schrift 432: Identifikation von Haltestellen (DHID)*. [S2.17]
- DELFI. (2025). *Zentrales Haltestellenverzeichnis (ZHV) — Erklärdokumentation*. [S2.17]
- VDV. (2018). *VDV-Schrift 453: Ist-Daten-Schnittstelle*, v2.6; VDV. (2013 **[verify]**) *VDV-Schrift 454*, v1.2.2. [S2.10, S2.11]
- VDV. (2019). *VDV-Schrift 431-2: TRIAS*, v1.3. [S2.12]
- OpenData ÖPNV. (2026). *Deutschlandweite Sollfahrplandaten (GTFS) — DELFI dataset*. [S2.15]
- gtfs.de. (2026). *GTFS für Deutschland (feeds generated from the DELFI dataset)*. [S2.16]
- Mobilithek. (2026). *National Access Point for Mobility Data in Germany*. [S2.14]
- Mobilitätsplattform Bayern. (2026). *DEFAS — Bayerische Mobilitätsplattform*. [S2.18]
- Kittelson & Associates, et al. (2003 **[verify]**). *Transit Capacity and Quality of Service Manual* (TCRP Report 100). TRB. [S5.5]

### Official documentation & practitioner sources (all: accessed 2026)
- PostGIS (2026); PostgreSQL (2026); Apache Parquet (2026); MongoDB (2026); ClickHouse docs — MergeTree family, HTTP interface, CREATE VIEW (2026); Apache Airflow (2026); Dagster (2026); Prefect (2026); Apache Flink (2026); Confluent — Schema evolution (2026); JSON Schema Initiative (2026); Great Expectations (2026); AWS — S3 API Reference (2026); RustFS (2026); DLR — Eclipse SUMO GTFS import (2026); matsim-org — GTFS2MATSim, pt2matsim (2026); DWD — Climate Data Center (2026); Azure Architecture Center — Event Sourcing pattern (2026). [S3.7, S3.8, S3.9, S3.10, S3.6, S5.2, S5.3, S4.10, S4.11, S4.12, S4.9, S4.30, S4.27, S4.29, S3.15, S3.16, S2.19, S2.20, S5.10, S1.4]
