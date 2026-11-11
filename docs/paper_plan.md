# Term Paper Plan — Domain 1: Data Engineering & Infrastructure
**Project:** Smart Mobility Würzburg (Master Project Seminar, WS 2026/27)  
**Target Length:** ~10 pages (excluding title page and references)

---

## Guiding Focus & Positioning

This plan structures a **technology- and concept-driven research paper**, not a low-level DDL manual (concrete table schemas remain in `gtfs_data_model.md` and `data_pipeline_plan.md`). 

In line with Phase 1 of `master_pjs.pdf` (*building deep domain expertise before collaborative implementation*), each core chapter follows a two-step pattern:
1. **Technology Evaluation:** Compare relevant standards, database paradigms, or pipeline concepts and their trade-offs in public transit data engineering.
2. **Contextual Application:** Justify a concrete architectural choice using the real constraints of the WVV dataset (5.1M APC Parquet rows, unstable weekly GTFS snapshots, unstructured 2026 PDF timetables, and downstream Simulation/ML needs).

### Core Thesis
Heterogeneous municipal mobility data—spanning historical sensor logs (*Ist*), multi-source schedules (*Soll*), contextual calendars, and future real-time streams—can be unified without complex GIS-transactional overhead by combining an **S3-based Lakehouse raw zone**, an append-only **Medallion layering convention**, and a **columnar OLAP engine (ClickHouse)**. Where standard feeds break down (export-unstable GTFS IDs and PDF-only 2026 timetables), **content-based fingerprinting** and **contract-validated LLM extraction** allow all sources to converge on a single, reproducible daily schedule and fact model.

---

## Page Budget & Seminar Alignment

| Section | Title | Target | `master_pjs.pdf` Criterion Covered | Suggested Visual / Table |
|---|---|---|---|---|
| **1** | Introduction & System Context | **1.0 p.** | Role of Domain 1, Spec-Driven approach | System context diagram (Domains 1–3 + Dashboard) |
| **2** | Mobility Data Sources & Standards | **2.0 p.** | *Evaluate data sources and formats* | Comparison table: GTFS vs. NeTEx & GTFS-RT vs. VDV/SIRI |
| **3** | Storage & Spatial Database Architectures | **2.0 p.** | *Compare spatial database architectures* | Decision matrix: PostGIS vs. NoSQL vs. Object Store + OLAP |
| **4** | ETL/ELT Pipeline & Continuous Processing | **2.5 p.** | *Design robust ETL pipelines for continuous processing* | End-to-end Medallion & fingerprinting flow diagram |
| **5** | Cross-Domain Data & API Contract | **1.5 p.** | *Define the API contract (Needs & Deliverables)* | Bidirectional interface contract table (D1 ↔ D2, D3, UI) |
| **6** | Critical Discussion & Conclusion | **1.0 p.** | Quality assurance, trade-offs, Phase 2 transition | — |
| **Total** | | **10.0 p.** | | *3 tables + 2 compact diagrams* |

---

## Section-by-Section Outline

### 1. Introduction & System Context (~1.0 page)
- **Motivation:** Public transport capacity planning and simulation require aligning *planned supply* (schedules) with *observed demand* (passenger counts) and *external drivers* (holidays, events, lectures).
- **Role of Domain 1:** Acts as the foundational data platform and interface owner for **Domain 2 (Traffic Simulation)**, **Domain 3 (Capacity Planning & ML)**, and the **Shared Visualization Dashboard**.
- **Core Requirements:**
  - *Functional:* Unified stop-event history, calendar-resolved daily schedules, joinable context features, and extensibility to continuous API feeds.
  - *Non-functional:* Reproducibility from immutable raw files, data provenance, append-only history (no destructive updates), and resilience to schema drift.

### 2. Mobility Data Sources & Exchange Standards (~2.0 pages)
*Focus: Understand the European/German transit data ecosystem and diagnose the concrete gaps in the WVV data landscape.*

- **Static Schedule Standards (GTFS vs. NeTEx/Transmodel):**
  - Compare **GTFS** (flat, CSV-based, de-facto standard for routing/simulation tools like SUMO and MATSim) against **NeTEx / Transmodel EN 12896** (hierarchical XML, rich `DayType` concepts, EU-mandated under Delegated Reg. 2017/1926 for National Access Points).
  - *Contextual Decision:* Adopt GTFS as the internal conceptual anchor—upstream historical archives (DELFI) arrive in GTFS, downstream simulators consume GTFS natively, and flat GTFS-like rows are deterministically validatable when extracting 2026 PDFs (unlike deeply nested NeTEx XML graphs).
- **Real-Time & Operational APIs (GTFS-RT vs. VDV/SIRI/TRIAS):**
  - Contrast **GTFS-RT** (lightweight Protobuf `TripUpdates` / `VehiclePositions` referencing static GTFS IDs) with German operator standards (**VDV 453/454**, **SIRI**, **TRIAS** exposed via regional hubs like DEFAS Bavaria). Note the lack of a single unified live stream for regional operators.
- **Assessment of WVV Project Sources:**
  - *Soll-Daten (Schedules):* Weekly Germany-wide DELFI GTFS snapshots (2022–2025; empirically verified 100% match against WVV's 2023 construction timetable, including replacement buses/SEV, but lacking stable cross-export IDs) + ~65 WVV timetable PDFs required to cover the 2026 gap.
  - *Ist-Daten (Observed Demand):* 5.1M APC/AVL stop-event rows in Parquet (2022–2026 across 40 lines), exhibiting empty placeholder files and schema drift (35 columns in 2022–2025 vs. 42 in 2026).
  - *Context Data:* Interval CSVs (Bavarian public/school holidays, university lectures, events) and hourly pedestrian street counters, plus potential external weather feeds for ML.

### 3. Storage & Spatial Database Architectures (~2.0 pages)
*Focus: Directly address the spatial database comparison criterion by matching database internals to actual mobility workloads.*

- **Workload Analysis:** Distinguish *topological GIS workloads* (routing, polygon intersections, map-matching—handled inside Domain 2's SUMO/MATSim frameworks) from Domain 1's *analytical data platform workload* (multi-million-row time-series scans, historical snapshot versioning, temporal joins, and bulk ML feature exports, where spatial attributes are primarily fixed stop coordinates).
- **Comparative Evaluation of Paradigms:**
  1. **Relational Spatial RDBMS (PostgreSQL / PostGIS):** Rich OGC spatial types, GiST spatial indexing, and strict ACID semantics. Strongest choice for interactive geospatial queries and road-network editing, but row-oriented storage incurs higher overhead on large analytical column scans and historical multi-snapshot deduplication.
  2. **NoSQL Stores (Document e.g. MongoDB / Wide-Column e.g. Cassandra):** High write throughput and flexible schemas for nested API payloads, but poorly suited for complex relational joins (`Ist × Soll × Calendar`) and ad-hoc OLAP aggregations.
  3. **Lakehouse Raw Storage + Columnar OLAP (S3 Object Store + ClickHouse):** Decouples cheap, immutable storage of heterogeneous raw files (Parquet, ZIP, PDF, JSON) via the S3 API (implemented via RustFS) from a vectorized, columnar analytical engine optimized for high compression, array types, and fast time-series scans.
- **Architectural Synthesis:** Justify **S3 + ClickHouse** for WVV based on analytical read performance, native `s3()` table functions, and append-only `MergeTree` versioning—while explicitly defining the boundary where PostGIS would become preferable (e.g., if Domain 1 took over OSM road-graph processing).

### 4. ETL/ELT Pipeline & Continuous Processing (~2.5 pages)
*Focus: Explain the data engineering patterns needed to turn messy, multi-speed transit sources into reliable, continuously updatable tables.*

- **Processing Paradigm & Orchestration:**
  - Compare **Streaming** (Kappa/Lambda with Kafka/Flink) vs. **Batch & Scheduled Micro-Batch**. At ~1.1M APC rows/year, weekly GTFS archives, and daily simulation calibration cycles, batch/micro-batch avoids streaming complexity while supporting continuous API polling.
  - Compare workflow orchestrators (**Apache Airflow** vs. **Dagster / Prefect** vs. cron): select DAG-based orchestration (Airflow) for retries, backfill scheduling, dependency tracking, and observability.
- **Medallion Layering (`Bronze → Silver → Gold`):**
  - Use immutable S3 buckets as the single source of truth (reproducibility), followed by logical Medallion layers in ClickHouse: `Bronze/Raw` (1:1 source fidelity + provenance metadata), `Silver/Clean` (type-harmonized, schema-unified, append-only evidence), and `Gold/Dim` (deduplicated business truth).
- **Domain-Specific Transformation Patterns:**
  - *Single-Point Calendar Resolution:* Expand GTFS `calendar` + `calendar_dates` rules and context holiday/lecture intervals once into concrete calendar dates so downstream consumers never implement calendar logic.
  - *Cross-Snapshot Entity Resolution (Content Fingerprinting):* Because DELFI GTFS regenerates `route_id` and `trip_id` on every export, identify unique trips via a deterministic hash (`fingerprint`) over stable attributes (`line`, terminus/direction, `stop_ids`, arrival/departure minutes). Retain all observations in Silver and resolve effective truth in Gold via `argMax(..., snapshot_date)`, yielding built-in revision flags (`was_corrected`) and confidence metrics (`snapshot_count`).
- **Integrating Unstructured & Continuous Feeds:**
  - *2026 PDF Extraction with Guardrails:* Explain why coordinate/rule-based PDF grid parsing fails across diverse timetable layouts (referencing preliminary findings) and how multimodal LLM extraction succeeds *only* when wrapped in a **deterministic validation contract** (known DHID stop list, monotonic stop sequences, valid time formats, explicit per-trip school-day footnotes)—ingested as a `source='pdf'` pseudo-snapshot into the identical Medallion flow.
  - *Continuous Real-Time Extension:* Adapter pattern landing raw GTFS-RT / TRIAS payloads in S3 and joining volatile live `trip_id`s to Gold fingerprints via snapshot lookup tables.

### 5. Cross-Domain Data & API Contract (~1.5 pages)
*Focus: Fulfill the "Domain Owner" specification requirement by clearly defining shared identifiers, deliverables, and upstream dependencies.*

- **Ubiquitous Join Keys:**
  - **Spatial / Stop Key:** Official German stop ID (`DHID`, e.g., `de:09663:*`), bridging GTFS, PDFs, simulation nodes, and APC stations.
  - **Network Key:** Stable GTFS `route_short_name` (incl. `SEV` replacement lines) + normalized direction/terminus.
  - **Temporal & Trip Keys:** ISO `service_date` (`Europe/Berlin` operating day, supporting >24:00 GTFS minutes) and content `fingerprint`.
- **What Domain 1 Provides (Outputs & Access Patterns):**
  - *To Domain 2 (Traffic Simulation — SUMO/MATSim):* Versioned stop coordinates (`gold_stop`), active line metadata (`route_type`), daily trip schedules with arrival and departure arrays (`arr_minutes`, `dep_minutes`), GTFS-compatible export views, and empirical APC boarding/dwell distributions for calibration.
  - *To Domain 3 (Capacity Planning & ML):* Schema-harmonized `clean.stop_events` (2022–2026), matched `Soll–Ist` trip views (for delay and utilization modeling), and pre-joined calendar/event/lecture/pedestrian feature tables.
  - *To Shared Dashboard:* Fast analytical SQL views for KPI visualization (line utilization, punctuality, schedule coverage) plus sink tables to store simulation scenarios and ML forecasts.
  - *Delivery Interface:* Read-only SQL views / HTTP interface in ClickHouse for interactive queries and dashboarding; reproducible Parquet/CSV exports in S3 for reproducible ML training and simulation runs.
- **What Domain 1 Needs (Inputs from Team & Stakeholders):**
  - *From Domain 2:* Whether GTFS `shapes.txt` geometries or custom OSM stop-to-link mappings must be persisted, plus output schemas for simulation runs.
  - *From Domain 3:* Target temporal/spatial aggregation grain, additional external feature requirements (e.g., DWD historical weather data), and schema for forecast/optimized schedule write-back.
  - *From WVV Stakeholders:* Clarification of undocumented APC fields (`quality_factor`, `passenger_*_measured` vs. `passenger_*`, raw Parquet timezone) and access details for live operational APIs.

### 6. Critical Discussion & Conclusion (~1.0 page)
- **Key Architectural Trade-offs:**
  - *Daily exploded schedule grain vs. compact date ranges:* Trades storage duplication (mitigated by columnar compression) for zero-cost temporal joins in ML and simulation.
  - *Content fingerprints:* Solves ID instability across snapshots, though minor minute-level retimings produce a new fingerprint (mitigated via `was_corrected` tracking at line/time-window level).
- **Limitations & Data Risks:** Undocumented APC sensor flags, potentially incomplete 2026 APC Parquet exports, manual review queue required for ambiguous PDF footnotes, and unconfirmed WVV coverage in national GTFS-RT feeds.
- **Conclusion & Phase 2 Outlook:** Summarize how separating raw object storage, append-only versioned transformations, and strict cross-domain contracts provides a maintainable foundation for Phase 2 implementation.

---

## Key References by Section

- **Sec. 1 (Principles & Provenance):** Wilkinson et al. (2016), *FAIR Guiding Principles* (Scientific Data); Batini & Scannapieco (2016), *Data and Information Quality*.
- **Sec. 2 (Transit Standards):** MobilityData *GTFS & GTFS-RT Reference*; CEN *Transmodel (EN 12896)* & *NeTEx*; *SIRI (EN 15531)* & VDV *453/454 / TRIAS*; EU Delegated Regulation 2017/1926; DELFI / OpenData ÖPNV documentation; SUMO & MATSim GTFS import docs.
- **Sec. 3 (Storage & Spatial DBs):** Armbrust et al. (2021), *Lakehouse: A New Generation of Open Platforms* (CIDR); Stonebraker et al. (2005), *C-Store: A Column-Oriented DBMS* (VLDB); PostGIS Documentation (*postgis.net*); ClickHouse Documentation (*MergeTree* architecture).
- **Sec. 4 (Pipelines, Versioning & LLM Extraction):** Kimball & Ross (2013), *The Data Warehouse Toolkit* (append-only / SCD concepts); Databricks *Medallion Architecture* (practitioner pattern); Marz & Warren (2015) & Kreps (2014) (Lambda vs. Kappa / batch vs. streaming); Apache Airflow / Dagster docs; Christophides et al. (2020), *End-to-End Entity Resolution for Big Data* (ACM Comput. Surv.); Lu et al. (2025) / Xu et al. (2024), *LLMs for Table Processing / Information Extraction*.
- **Sec. 5 & 6 (Transit Data Quality):** APC validation literature (e.g., *Transportation Research Record* studies on Automatic Passenger Counting bias and quality filtering).
