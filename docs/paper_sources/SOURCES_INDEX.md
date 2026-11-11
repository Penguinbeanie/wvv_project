# Sources Index — Smart Mobility Würzburg Term Paper (Domain 1)

**Purpose:** Complete manifest of every source needed to write the term paper offline (10 h, no wifi).
Nothing has been downloaded — **you download everything yourself** from the URLs below before the flight.

Companion to: `docs/paper_plan.md` (section numbers and sub-bullets below refer to that plan).

---

## Legend

| Tag | Meaning |
|---|---|
| **[CORE]** | Download before the flight — actively cited or needed while writing |
| **[OPT]** | Nice-to-have backup / background; skip if time is short |
| **OPEN-PDF** | Direct PDF download link, no login |
| **WEB** | HTML page — use "Print → Save as PDF" so you have it offline |
| **PAYWALL** | University login / VPN or purchase needed (get it *before* leaving home) |
| **BOOK** | Physical/e-book; check university library |
| **FREE-REG** | Free but requires registration |
| `Filename` | Suggested name to save the file as, so it matches this index |

Priority download order: the checklist in the next section covers all must-haves.

---

## A. Pre-Flight Download Checklist (direct PDFs, ~20 min)

Grab these first — they are direct PDF links with no login behind them:

1. Lakehouse (CIDR 2021) → `S3.1_Lakehouse_CIDR2021.pdf` … https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf
2. C-Store (VLDB 2005) → `S3.2_C-Store_VLDB2005.pdf` … https://www.vldb.org/archives/website/2005/program/paper/thu/p553-stonebraker.pdf
3. MonetDB/X100 (CIDR 2005) → `S3.3_MonetDB-X100.pdf` … https://www.cidrdb.org/cidr2005/papers/P19.pdf
4. Column-store survey (Abadi et al.) → `S3.4_Column-Stores-Survey.pdf` … https://www.cs.umd.edu/~abadi/papers/abadi-column-stores.pdf
5. ClickHouse PVLDB 2024 paper → `S3.5_ClickHouse_PVLDB2024.pdf` … https://www.vldb.org/pvldb/vol17/p3731-schulze.pdf
6. Entity Resolution survey (arXiv) → `S4.15_EntityResolution_CSUR2020.pdf` … https://arxiv.org/pdf/1905.06397
7. Xu et al. LLM-IE survey → `S4.19_Xu_LLM-GenerativeIE.pdf` … https://arxiv.org/pdf/2312.17617
8. Lu et al. LLM table survey → `S4.20_Lu_LLM-Table-Processing.pdf` … https://arxiv.org/pdf/2402.05121
9. LLMs on tabular data survey → `S4.21_LLM-Tabular-Data-Survey.pdf` … https://arxiv.org/pdf/2402.17944
10. Table detection/recognition survey → `S4.22_TableDetectionSurvey.pdf` … https://arxiv.org/pdf/2211.08469
11. Hallucination survey → `S4.26a_LLM-Hallucination-Survey.pdf` … https://arxiv.org/pdf/2311.05232
12. Multimodal hallucination survey → `S4.26b_MLLM-Hallucination-Survey.pdf` … https://arxiv.org/pdf/2404.18930
13. Recurring Public Transit Schedules (2026) → `S4.17_Recurring-Schedules-StableID.pdf` … https://arxiv.org/pdf/2606.14713
14. rt2gtfs (2026) → `S4.18_rt2gtfs.pdf` … https://arxiv.org/pdf/2603.11477
15. FAIR principles (Nature, open access) → `S1.1_FAIR.pdf` … https://www.nature.com/articles/sdata201618.pdf
16. TCRP Report 113 (AVL/APC) → `S5.4_TCRP113_AVL-APC.pdf` … https://www.trb.org/publications/tcrp/tcrp_rpt_113.pdf
17. TCRP Web Doc 23 → `S5.4b_TCRP-WebDoc23.pdf` … https://trb.org/publications/tcrp/tcrp_webdoc_23.pdf
18. TRR 1308 APC evaluation (1991) → `S5.7_TRR1308_APC-Eval-1991.pdf` … https://onlinepubs.trb.org/Onlinepubs/trr/1991/1308/1308-010.pdf
19. European APC accuracy study (open) → `S5.8_APC-European-Bus.pdf` … https://opentransportationjournal.com/VOLUME/13/PAGE/250/FULLTEXT/
20. GTFS ↔ NeTEx mapping (DATA4PT) → `S2.7_GTFS-NeTEx-Mapping.pdf` … https://transmodel-cen.eu/wp-content/uploads/2024/06/2024-June_DATA4PT_GTFS-NeTEx-Mapping_vf.pdf
21. VDV 432 (DHID spec, German) → `S2.17a_VDV432_DHID.pdf` … https://www.vdv.de/downloads/3855/432SDS/forced
22. VDV 453 SDS (German) → `S2.10a_VDV453_v2.6.pdf` … https://www.vdv.de/453v2.6-sds.pdfx
23. VDV 454 SDS (German) → `S2.11a_VDV454_v1.2.2.pdf` … https://www.vdv.de/454v1.2.2-sds.pdf.pdfx
24. Making Sense of Stream Processing (free ebook) → `S4.7_Kreps_StreamProcessing.pdf` … https://assets.confluent.io/m/2a60fabedb2dfbb1/original/20190307-EB-Making_Sense_of_Stream_Processing_Confluent.pdf
25. MATSim book (open access) → `S2.20c_MATSim-Book_2016.pdf` … https://library.oapen.org/handle/20.500.12657/32162
26. AWS S3 API reference (official PDF) → `S3.15b_S3-API.pdf` … https://docs.aws.amazon.com/pdfs/AmazonS3/latest/API/s3-api.pdf

Then, from the per-section lists below, save the **[WEB]** documentation pages as PDFs (browser: Print → Save as PDF) — GTFS reference, GTFS-RT proto, ClickHouse engine pages, PostGIS, Databricks medallion, orchestrator docs, SIRI/NeTEx GitHub wikis, etc.

**Paywalled to fetch via university VPN/library before you leave:** Batini & Scannapieco book (S1.3), Kimball & Ross book (S4.1), Marz & Warren book (S4.5), TRR 1835 APC paper (S5.6), Lu et al. FCS published version (S4.20, arXiv version is free), Fellegi & Sunter (S4.16 [OPT]).

---

## B. Sources by Paper Section

### §1 Introduction & System Context (data-engineering principles, provenance, quality)

**S1.1 [CORE] Wilkinson et al. (2016): The FAIR Guiding Principles for scientific data management and stewardship.** *Scientific Data* 3:160018.
- URL: https://www.nature.com/articles/sdata201618 (OPEN-PDF, CC-BY)
- Filename: `S1.1_FAIR.pdf`
- For: §1 non-functional requirements (reproducibility from immutable raw files, provenance, findability).
- How: cite when introducing the "immutable S3 raw zone as single source of truth" principle; map F/A/I/R onto your bronze-layer provenance metadata. Also usable in §6 conclusion for "reproducible foundation".

**S1.2 [OPT] GO FAIR — FAIR Principles overview.**
- URL: https://www.go-fair.org/fair-principles/ (WEB)
- Filename: `S1.2_GO-FAIR.pdf`
- For: §1.
- How: quick offline cheat-sheet of all 15 principles while writing §1 without needing the paper open; not necessarily cited.

**S1.3 [CORE] Batini, C. & Scannapieco, M. (2016): Data and Information Quality: Dimensions, Principles and Techniques.** Springer.
- URL: https://link.springer.com/book/10.1007/978-3-319-24106-7 (BOOK/PAYWALL — university library)
- Free author/edition preview PDF: https://content.e-bookshelf.de/media/reading/L-5007989-a3bfb8fc03.pdf (OPEN-PDF)
- Filename: `S1.3_Batini-Scannapieco_DIQ.pdf`
- For: §1 (quality as a first-class platform requirement) and §6 (limitations discussion: accuracy/completeness dimensions for undocumented APC flags).
- How: cite the dimensions framework when you argue that APC `quality_factor`-type fields need documented semantics; use the preview PDF (pre+TOC) if you cannot get the e-book.

**S1.4 [CORE] Microsoft Azure Architecture Center: Event Sourcing pattern.**
- URL: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing (WEB)
- Filename: `S1.4_EventSourcing-Pattern.pdf`
- For: §1 (append-only history, no destructive updates) and §4.2 (Medallion append-only evidence).
- How: canonical citation that append-only immutable event streams are an established architectural pattern — supports your "Silver keeps all observations, Gold resolves truth" argument.

**S1.5 [CORE-§5] Dehghani, Z. — Data Mesh (articles).**
- URLs: https://martinfowler.com/articles/data-mesh-principles.html and https://martinfowler.com/articles/data-monolith-to-mesh.html (WEB)
- Filename: `S1.5_DataMesh-Principles.pdf`, `S1.5b_Monolith-to-Mesh.pdf`
- For: §1 (Domain 1–3 ownership framing) and §5 (data-as-a-product, cross-domain contract rationale).
- How: cite "domain ownership" + "data as a product" when defining the interface-owner role of D1 towards D2/D3/dashboard; strongest theoretical anchor for the API-contract chapter.

---

### §2 Mobility Data Sources & Exchange Standards (GTFS vs NeTEx, GTFS-RT vs VDV/SIRI, DELFI, simulators)

**S2.1 [CORE] MobilityData — GTFS Schedule Reference.**
- URL: https://gtfs.org/documentation/schedule/reference/ (WEB)
- Filename: `S2.1_GTFS-Schedule-Reference.pdf`
- For: §2.1 comparison table (GTFS column), §4.4.1 calendar resolution, §5 ISO/`service_date` temporal keys.
- How: primary normative source for every GTFS field claim: `calendar`/`calendar_dates` semantics, `exact_times`, `>24:00` time handling, `route_short_name`, `shapes.txt`. Quote the service-day definition when justifying Europe/Berlin operating-day key.

**S2.2 [CORE] MobilityData — GTFS Schedule Best Practices.**
- URL: https://gtfs.org/documentation/schedule/schedule-best-practices/ (WEB)
- Filename: `S2.2_GTFS-Best-Practices.pdf`
- For: §4.4.2 (ID-stability problem statement for fingerprinting).
- How: the Best Practices *require* stable IDs — pairing this with the observed DELFI re-generated IDs (and S2.4 PR below) documents the gap your fingerprint solves.

**S2.3 [CORE] MobilityData — GTFS Realtime Protobuf Reference.**
- URL: https://gtfs.org/documentation/realtime/proto/ (WEB)
- Filename: `S2.3_GTFS-Realtime-Proto.pdf`
- For: §2.2 comparison table (GTFS-RT column), §4.4.2 continuous real-time extension adapter.
- How: `TripUpdate`/`VehiclePosition`/`ServiceAlert` structure and the rule that RT `trip_id` references static GTFS — the basis for your "join volatile live IDs to Gold fingerprints via snapshot lookup" argument.

**S2.4 [OPT] MobilityData — GTFS Realtime Best Practices (GitHub).**
- URL: https://github.com/MobilityData/GTFS_Realtime_Best-Practices (WEB)
- Filename: `S2.4_GTFS-RT-Best-Practices.pdf`
- For: §2.2, §4.4.2 (feed polling hygiene, frequency of polling, deduplication of feed entities).

**S2.5 [CORE] google/transit — the GTFS spec repository (incl. open issue "ID stability").**
- URL: https://github.com/google/transit/pull/171 (WEB — pull request "Define and require ID stability for agency_id, route_id, stop_id")
- Filename: `S2.5_GTFS-ID-Stability-PR171.pdf`
- For: §4.4.2 cross-snapshot entity resolution — *practitioner evidence* that ID instability across exports is a recognized, unresolved problem.
- How: strongest citable evidence outside the empirical DELFI finding; quote maintainers discussing why IDs churn.

**S2.6 [CORE] NeTEx — CEN/TS 16614 (GitHub + overview).**
- URLs: https://github.com/TransmodelEcosystem/NeTEx (schemas, WEB) · overview: https://en.wikipedia.org/wiki/NeTEx (WEB)
- Filename: `S2.6_NeTEx-GitHub.pdf`, `S2.6b_NeTEx-Wiki.pdf`
- For: §2.1 comparison table (NeTEx column): hierarchical XML, DayTypes, versioned frames.
- How: point to the XSD structure to support "deeply nested graphs are hard to validate deterministically" vs flat CSV rows. GitHub carries the actual schemas — no purchase needed (full CEN text is paywalled; see access note).

**S2.7 [CORE] DATA4PT — Outline comparison and mapping between NeTEx & GTFS (CEN, 2024).**
- URL: https://transmodel-cen.eu/wp-content/uploads/2024/06/2024-June_DATA4PT_GTFS-NeTEx-Mapping_vf.pdf (OPEN-PDF)
- Mirror: https://data4pt-project.eu/wp-content/uploads/2024/06/GTFS-NeTEx-Mapping-nk-v5.pdf
- Filename: `S2.7_GTFS-NeTEx-Mapping.pdf`
- For: §2.1 — the back pocket source for the GTFS-vs-NeTEx comparison table; states that all GTFS+RT information is covered by NeTEx/SIRI.
- How: use its feature mapping to argue *coverage parity but representation asymmetry*; cite as EU-project documentation, not peer-reviewed paper.

**S2.8 [CORE] Transmodel (EN 12896) — official site + key-elements PDF.**
- URLs: https://transmodel-cen.eu/ (WEB) · https://transmodel-cen.eu/wp-content/uploads/2024/05/5-KB_Key-elements-of-Transmodel-standard.pdf (OPEN-PDF) · https://en.wikipedia.org/wiki/Transmodel (WEB)
- Filename: `S2.8_Transmodel-Site.pdf`, `S2.8b_Key-Elements.pdf`
- For: §2.1 (NeTEx is the XML embodiment of Transmodel; `DayType` concepts).
- How: cite for the conceptual model argument (NeTEx = exchange syntax over Transmodel ontology); also supports your "GTFS as internal anchor ≠ rejecting Transmodel concepts" nuance.

**S2.9 [CORE] SIRI (EN 15531) — schemas + overview.**
- URLs: https://github.com/SIRI-CEN/SIRI (WEB) · https://www.siri.org.uk/schema/schemas.htm (schemas & docs listing, WEB) · https://en.wikipedia.org/wiki/Service_Interface_for_Real_Time_Information (WEB)
- Filename: `S2.9_SIRI-GitHub.pdf`, `S2.9b_SIRI-Schemas-Page.pdf`, `S2.9c_SIRI-Wiki.pdf`
- For: §2.2 comparison table (SIRI column), §4.4.2 (German hubs speak SIRI/TRIAS, not GTFS-RT).
- How: shows SIRI's richer operational semantics (e.g., production timetables, estimated calls) vs GTFS-RT's lightweight protobuf — supports the "no single unified live feed for regional operators" statement when contrasted with DEFAS (S2.20).

**S2.10 [CORE] VDV 453 — Ist-Daten-Schnittstelle (specification PDFs, German).**
- URLs: https://www.vdv.de/ist-daten-schnittstellen.aspx (overview, WEB) · https://www.vdv.de/453v2.6-sds.pdfx (v2.6 04/2018, OPEN-PDF) · older: https://www.vdv.de/453v2.3.2-sds.pdf.pdfx · downloads portal: https://www.vdv.de/i-d-s-downloads.aspx (WEB)
- Filename: `S2.10a_VDV453_v2.6.pdf`
- For: §2.2 (VDV 453/454 row of the German-standards comparison).
- How: defines the stop-level real-time datum (Ankunfts-/Abfahrtszeiten, Ausfall) German operators exchange; explains why raw German operator telemetry cannot feed GTFS-RT consumers directly.

**S2.11 [OPT] VDV 454 — Ist-Daten-Schnittstelle on basis of VDV 453.**
- URL: https://www.vdv.de/454v1.2.2-sds.pdf.pdfx (OPEN-PDF, German)
- Filename: `S2.11a_VDV454_v1.2.2.pdf`
- For: §2.2 (distinguishes 453 vs 454 division of labor).
- How: cite if you detail the German standard family; otherwise one combined VDV sentence referencing both PDFs suffices.

**S2.12 [CORE] TRIAS (VDV 431-1/-2) — GitHub schemas + VDV pages.**
- URLs: https://github.com/VDVde/TRIAS (WEB — official `VDVde` schema repo incl. `Trias.xsd`) · https://www.vdv.de/ip-kom-oev.aspx (WEB — IP-KOM-ÖV project origin) · https://www.vdv.de/431-2sdes-v-1-3.pdfx (431-2 technical doc, OPEN-PDF German)
- Filename: `S2.12_TRIAS-GitHub.pdf`, `S2.12b_TRIAS-431-2.pdf`
- For: §2.2 (TRIAS row: request/response travel-information protocol layered on Siri-SX/PT).
- How: TRIAS = what regional hubs (e.g., DEFAS, Nahverkehrshessen) actually expose; justifies the "adapter pattern landing raw TRIAS payloads in S3" in §4.4.2.

**S2.13 [CORE] Commission Delegated Regulation (EU) 2017/1926 (EU-wide real-time traffic information).**
- URL: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R1926 (WEB) · consolidated 2024 version: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02017R1926-20240304
- Filename: `S2.13_EU-Reg-2017-1926.pdf`
- For: §2.1 (EU mandate for NeTEx/SIRI via National Access Points); background for "DELFI arrives in GTFS anyway" tension.
- How: quote the accessibility/RTTI obligations; EUR-Lex offers PDF download directly on the page.

**S2.14 [OPT] Germany's National Access Point (Mobilithek) + ITS national report.**
- URLs: https://mobilithek.info/ (WEB) · BMV English overview: https://www.bmv.de/SharedDocs/EN/Articles/G/mobilithek.html (WEB) · https://transport.ec.europa.eu/document/download/f8d0301e-b692-44a3-9804-c7a8388353ea_en?filename=2019-its-national-report-germany.pdf (OPEN-PDF)
- Filename: `S2.14_Mobilithek-Site.pdf`, `S2.14b_ITS-National-Report-DE-2019.pdf`
- For: §2.1 regulatory context; §2 "assessment of WVV sources" (where DELFI data is published).
- How: one sentence of German NAP context; the national report PDF is handy proof that NAP mandate ≠ uniform GTFS-RT coverage.

**S2.15 [CORE] DELFI — deutschlandweite Sollfahrplandaten (GTFS) via OpenData ÖPNV.**
- URLs: portal: https://www.opendata-oepnv.de/ (WEB — navigate: Organisation → DELFI → "deutschlandweite Sollfahrplandaten (GTFS)") · GovData entry: https://data.gov.de/suche/daten/delfi-timetable-gtfs (WEB)
- Filename: `S2.15_DELFI-Dataset-Page.pdf`
- For: §2 assessment of Soll sources (weekly snapshots 2022–2025, SEV coverage), §4.4.2 (snapshot cadence/ID churn).
- How: cite the dataset + your own empirical 2023-timetable verification; save the dataset description page (it documents the DELFI integration platform DIP producing the feed).

**S2.16 [OPT] gtfs.de — GTFS feeds for Germany (generated from DELFI NeTEx).**
- URL: https://gtfs.de/de/feeds/de_full/ (WEB)
- Filename: `S2.16_gtfs-de.pdf`
- For: §2 — states explicitly the DELFI interchange happens in NeTEx and GTFS is derived.
- How: useful footnote source if your project consumed gtfs.de archives; also evidence for the "GTFS as derived de-facto interchange format" argument.

**S2.17 [CORE] VDV 432 — Identifikation von Haltestellen (DHID spec, German).**
- URLs: https://www.vdv.de/downloads/3855/432SDS/forced (Schnittstellendokument, OPEN-PDF) · supplement: https://www.vdv.de/downloads/3340/432%20%20SDK · DELFI ZHV explanation: https://www.delfi.de/media/zhv-erklaerdokument_04.09.2025_final.pdf (OPEN-PDF)
- Filename: `S2.17a_VDV432_SDH.pdf`, `S2.17b_ZHV-Dokumentation.pdf`
- For: §5 join keys (DHID `de:09663:*`), §2 stop-data assessment.
- How: defines the exact DHID format (`de:<AGS>:<ID>`) + ZHV (Central Stop Register) mapping — the bedrock citation for your ubiquitous spatial join key. Note: the plan says "VDV 467", but the operative DHID standard per VDV's own pages is **Schrift 432 (07/2016)** — check your other seminar materials and cite whichever the DELFI ZHV document actually references (it builds on IFOPT EN 28701; purchasable via national bodies: https://www.en-standard.eu/ — catalog only).

**S2.18 [CORE] DEFAS Bayern — Bavarian real-time/distribution platform.**
- URLs: https://mobilitaetsplattform.bayern/de/defas (WEB) · data offer: https://www.bayerninfo.de/datenangebot/daten-oev (WEB)
- Filename: `S2.18_DEFAS-Bayern.pdf`, `S2.18b_BayernInfo-DatenOeV.pdf`
- For: §2.2 regional-hub landscape (TRIAS hub used by WVV-region operators), §4.4.2 continuous-feed extension, §6 data risk (unconfirmed WVV coverage in national GTFS-RT feeds).
- How: cite as the concrete Bavarian hub for live data; pairs with TRIAS (S2.12) — both are Bavarian-context examples.

**S2.19 [CORE] SUMO — GTFS import tooling (official docs).**
- URLs: https://sumo.dlr.de/docs/Tools/Import/GTFS.html (WEB) · tutorial: https://sumo.dlr.de/docs/Tutorials/GTFS.html (WEB — `gtfs2pt.py` usage)
- Filename: `S2.19_SUMO-GTFS.pdf`, `S2.19b_SUMO-GTFS-Tutorial.pdf`
- For: §2 decision "GTFS as internal anchor because simulators consume it natively", §3 workload demarcation vs Domain 2, §5 D2 deliverables (GTFS-compatible export views).
- How: normative evidence that D2's toolchain ingests GTFS-shaped schedules (stop times as arrays/flows — mirrors your `arr_minutes`/`dep_minutes` design).

**S2.20 [CORE] MATSim — GTFS converters + open-access book.**
- URLs: https://github.com/matsim-org/GTFS2MATSim (WEB) · https://github.com/matsim-org/pt2matsim (WEB) · book landing: https://matsim.org/the-book/ (WEB) · full text (open access): https://library.oapen.org/handle/20.500.12657/32162 (OPEN-PDF)
- Filename: `S2.20a_GTFS2MATSim.pdf`, `S2.20b_pt2matsim.pdf`, `S2.20c_MATSim-Book_2016.pdf`
- For: same as S2.19; book chapter also supports §1 motivation (simulations need supply+demand calibration).
- How: cite the book (Horni/Nagel/Axhausen 2016, Springer, open access) for MATSim's transit-schedule model; cite gtfs loaders for GTFS-native ingestion.

**S2.21 [OPT] Pre-study and insights to a sequential MATSim-SUMO toolchain (SUMO Conference 2020).**
- URL: https://eclipse.dev/sumo/documents/2020/SUMO2020_paper_44.pdf (OPEN-PDF)
- Filename: `S2.21_MATSim-SUMO-Toolchain.pdf`
- For: §1 system context diagram justification (D1 serving D2 with GTFS outputs), §5 interface design.
- How: shows the two simulators chained in one pipeline — supports your claim that GTFS-shaped exports serve the whole D2 ecosystem.

**S2.22 [OPT] WVV / City of Würzburg pages (background, not academic references).**
- URLs: https://www.wvv.de/mobil-b2c/oepnv/ · https://www.wuerzburg.de/themen/verkehr--mobilitaet/fahrplanauskunft
- Filename: `S2.22_WVV-Context.pdf`
- For: §1 motivation (who WVV is), §2 source landscape.
- How: context only — do not use as scholarly citation; useful to footnote the operator's public schedule portal (source of the ~65 PDFs).

---

### §3 Storage & Spatial Database Architectures (PostGIS vs NoSQL vs S3+OLAP)

**S3.1 [CORE] Armbrust, Ghodsi, Xin, Zaharia (2021): Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics.** CIDR 2021.
- URL: https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf (OPEN-PDF) · author mirror: https://people.eecs.berkeley.edu/~matei/papers/2021/cidr_lakehouse.pdf
- Filename: `S3.1_Lakehouse_CIDR2021.pdf`
- For: §3 decision-matrix framing (lakehouse = open file formats + metadata layer on object stores), also §4 raw-zone rationale.
- How: cite for "decouple cheap immutable object storage from compute engines" — use it to describe bronze-layer reproducibility without claiming you use Delta/Iceberg (you deliberately use raw Parquet + ClickHouse instead of a table format; the paper's arguments still back the storage/compute split).

**S3.2 [CORE] Stonebraker et al. (2005): C-Store: A Column-oriented DBMS.** VLDB 2005.
- URL: https://www.vldb.org/archives/website/2005/program/paper/thu/p553-stonebraker.pdf (OPEN-PDF) · mirror: https://web.stanford.edu/class/cs345d-01/rl/cstore.pdf
- Filename: `S3.2_C-Store_VLDB2005.pdf`
- For: §3 paradigm comparison intro (column-stores are read-optimized for analytical scans vs row-oriented OLTP).
- How: historical anchor for the columnar argument; pair with S3.4 for the modern survey. Quote the projections/column-compression argument for MergeTree parts.

**S3.3 [OPT] Boncz, Zukowski, Nes (2005): MonetDB/X100: Hyper-Pipelining Query Execution.** CIDR 2005.
- URL: https://www.cidrdb.org/cidr2005/papers/P19.pdf (OPEN-PDF)
- Filename: `S3.3_MonetDB-X100.pdf`
- For: §3 ClickHouse justification ("vectorized" engine).
- How: the origin of vectorized execution — cite when you claim vectorized scans make ClickHouse fast on 5.1M-row time-series aggregations.

**S3.4 [CORE] Abadi, Boncz, Harizopoulos, Idreos, Madden (2013): The Design and Implementation of Modern Column-Oriented Database Systems.** *Foundations and Trends in Databases* 5(3):197–280.
- URL: https://www.cs.umd.edu/~abadi/papers/abadi-column-stores.pdf (OPEN-PDF)
- Filename: `S3.4_Column-Stores-Survey.pdf`
- For: §3 synthesis paragraph on analytical workloads (compression, late materialization, encoding).
- How: single best survey citation for "columnar OLAP engine for multi-million-row time-series scans"; cite alongside the Lakehouse paper.

**S3.5 [CORE] Schulze et al. (2024): ClickHouse — Lightning Fast Analytics for Everyone.** PVLDB 17(12):3731–3744.
- URL: https://www.vldb.org/pvldb/vol17/p3731-schulze.pdf (OPEN-PDF) · ACM DOI: https://dl.acm.org/doi/10.14778/3685800.3685802
- Filename: `S3.5_ClickHouse_PVLDB2024.pdf`
- For: §3 — the peer-reviewed citation specifically for ClickHouse (sparse index, MergeTree parts, arrays, compression).
- How: cite this rather than only marketing docs when making performance claims; then use product docs (S3.6) for concrete feature details.

**S3.6 [CORE] ClickHouse documentation — MergeTree family.**
- URLs: MergeTree: https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/mergetree (WEB) · ReplacingMergeTree: https://clickhouse.com/docs/engines/table-engines/mergetree-family/replacingmergetree (WEB) · argMax: https://clickhouse.com/docs/sql-reference/aggregate-functions/reference/argmax (WEB) · developer guide: https://github.com/ClickHouse/clickhouse-docs/blob/main/docs/guides/developer/replacing-merge-tree.md (WEB)
- Filename: `S3.6_MergeTree.pdf`, `S3.6b_ReplacingMergeTree.pdf`, `S3.6c_argMax.pdf`
- For: §3 (append-only MergeTree versioning; get "versioning without destructive updates" right) and §4.4.2 (`argMax`/`was_corrected` Gold truth).
- How: technical reference while writing; quote part-merging semantics carefully (asynchronous merges → why Gold queries must use `argMax(...)`/`FINAL` rather than assuming instant dedup.

**S3.7 [CORE] PostGIS — Official documentation.**
- URLs: https://postgis.net/documentation/ (WEB) · manual: https://postgis.net/docs/ (WEB)
- Filename: `S3.7_PostGIS-Manual.pdf`
- For: §3 paradigm-1 paragraph (OGC geometry types, GiST indexing, PostgreSQL extension).
- How: cite for "rich OGC spatial types + spatial indexing exist and are mature" — the fair-treatment part of the PostGIS column before you argue why analytical workloads point elsewhere.

**S3.8 [OPT] PostgreSQL manual — GiST indexes chapter.**
- URL: https://www.postgresql.org/docs/current/gist.html (WEB)
- Filename: `S3.8_PG-GiST.pdf`
- For: §3 PostGIS row (internals of the spatial index).
- How: only if you go one level deeper than "PostGIS uses GiST"; otherwise S3.7 suffices.

**S3.9 [CORE] Apache Parquet — File format specification.**
- URLs: https://parquet.apache.org/docs/file-format/ (WEB) · https://github.com/apache/parquet-format/ (WEB — thrift definitions)
- Filename: `S3.9_Parquet-Format.pdf`
- For: §2 (APC Parquet source), §3 (columnar raw-file format on S3), §5 (Parquet export deliverable to D3).
- How: cite for encoding/compression + self-describing schema — also supports schema-drift analysis (35 vs 42 columns across 2022–2026 exports).

**S3.10 [CORE] MongoDB — Database Manual.**
- URL: https://www.mongodb.com/docs/manual/ (WEB)
- Filename: `S3.10_MongoDB-Manual.pdf`
- For: §3 paradigm-2 row (document store; schema flexibility for nested payloads; weak cross-collection joins).
- How: cite the docs' own aggregation/join capabilities page to keep the criticism accurate and fair.

**S3.11 [CORE] Lakshman & Malik (2010): Cassandra — A Decentralized Structured Storage System.** *ACM SIGOPS Operating Systems Review* 44(2).
- URL: https://www.cs.cornell.edu/projects/ladis2009/papers/lakshman-ladis2009.pdf (OPEN-PDF) · ACM: https://dl.acm.org/doi/10.1145/1773912.1773922
- Filename: `S3.11_Cassandra.pdf`
- For: §3 paradigm-2 row (wide-column store; write throughput;JOIN-cost argument).
- How: cite as the canonical wide-column reference; contrast "tunable consistency + partitioned row store" with your relational join needs (`Ist × Soll × Calendar`).

**S3.12 [OPT] Chang et al. (2006): Bigtable — A Distributed Storage System for Structured Data.** OSDI 2006.
- URL: https://research.google.com/archive/bigtable-osdi06.pdf (OPEN-PDF)
- Filename: `S3.12_Bigtable.pdf`
- For: §3 NoSQL lineage (wide-column ancestor; LSM-tree-style writes).
- How: optional depth for the NoSQL paragraph; can be cited together with Cassandra in one sentence.

**S3.13 [OPT] DeCandia et al. (2007): Dynamo — Amazon's Highly Available Key-value Store.** SOSP 2007.
- URL: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf (OPEN-PDF)
- Filename: `S3.13_Dynamo.pdf`
- For: §3 availability-vs-consistency trade-off sentence (why AP stores still don't solve ad-hoc OLAP joins).
- How: optional; use if you want an explicit consistency-model comparison (DynamoAP vs PostGIS ACID).

**S3.14 [OPT] Davoudian, Chen, Liu (2018): A Survey on NoSQL Stores.** *ACM Computing Surveys* 51(2).
- URL: https://dl.acm.org/doi/10.1145/3158661 (WEB; open access via ACM)
- Filename: `S3.14_NoSQL-Survey.pdf`
- For: §3 paradigm-2 overall framing (data models, consistency, query expressiveness).
- How: cite at the head of the NoSQL paragraph to carry the category claims; then individual papers for specifics.

**S3.15 [CORE] AWS — S3 API Reference (the interface RustFS implements).**
- URL: https://docs.aws.amazon.com/AmazonS3/latest/API/Type_API_Reference.html (WEB) · official offline PDF: https://docs.aws.amazon.com/pdfs/AmazonS3/latest/API/s3-api.pdf (OPEN-PDF)
- Filename: `S3.15a_S3-API-Reference.pdf`, `S3.15b_S3-API.pdf`
- For: §3 paradigm-3 + §4 (S3 buckets as immutable raw landing zone; object durability/consistency context).
- How: cite "S3-compatible API = open, de-facto object-storage standard"; AWS explicitly offers this PDF for offline reading.

**S3.16 [OPT] RustFS — S3-compatible open-source object store (project docs).**
- URLs: https://github.com/rustfs/rustfs (WEB) · https://docs.rustfs.com/en (WEB)
- Filename: `S3.16_RustFS-Docs.pdf`
- For: §3/§4 when naming your concrete raw-zone implementation.
- How: footnote-grade citation for the chosen storage software; not needed if you keep the paper tool-agnostic ("S3-compatible object storage").

---

### §4 ETL/ELT Pipeline & Continuous Processing (orchestration, medallion, fingerprinting, LLM extraction)

**S4.1 [CORE] Kimball, R. & Ross, M. (2013): The Data Warehouse Toolkit, 3rd ed.** Wiley.
- URL: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/books/data-warehouse-dw-toolkit/ (WEB) · Wiley: https://www.wiley.com/en-us/The+Data+Warehouse+Toolkit:+The+Definitive+Guide+to+Dimensional+Modeling,+3rd+Edition-p-9781118530801
- Filename: `S4.1_Kimball-DW-Toolkit-3rd.pdf` (BOOK — library/e-book)
- For: §4 Gold-layer design (bus-matrix style fact/dim), SCD Type 2 analog of your append-only Silver→Gold pattern.
- How: cite when you declare Gold dims (`gold_stop`, line, date) as conformed dimensions for D2/D3; the free SCD articles (S4.2) carry the append-only argument if the book is unavailable.

**S4.2 [CORE] Kimball Group — Slowly Changing Dimensions articles (free).**
- URLs: https://www.kimballgroup.com/2008/08/slowly-changing-dimensions/ · https://www.kimballgroup.com/2008/09/slowly-changing-dimensions-part-2/ · Design Tip #152: https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/ (WEB)
- Filename: `S4.2a_Kimball-SCD-Part1.pdf`, `S4.2b_Kimball-SCD-Part2.pdf`, `S4.2c_Kimball-DesignTip152.pdf`
- For: §4.4 — "retain all observations, resolve effective truth" = standard dimensional practice, reinvented atop MergeTree.
- How: quote Type 2 validity windows → maps to your `argMax(..., snapshot_date)` + `was_corrected` revision mechanism.

**S4.3 [CORE] Databricks — What is the medallion lakehouse architecture?**
- URL: https://docs.databricks.com/aws/en/lakehouse/medallion (WEB) · blog version: https://www.databricks.com/blog/what-is-medallion-architecture
- Filename: `S4.3_Medallion-Databricks.pdf`
- For: §4.2 — definitional source for Bronze/Silver/Gold (raw → validated → enriched).
- How: cite as the practitioner-canon origin of the layering convention; Note: your implementation maps layers to ClickHouse schemas over immutable S3 rather than Delta tables — say so explicitly to stay honest.

**S4.4 [OPT] Critical counterpoints on the Medallion pattern (for §6 discussion).**
- URLs: Daniel Beach, "Medallion Architecture. Truth or Fiction?" https://dataengineeringcentral.substack.com/p/medallion-architecture-truth-or-fiction · "Beyond the Medallion" https://blog.matterbeam.com/beyond-the-medallion-rethinking-data-architecture-from-first-principles/ (WEB)
- Filename: `S4.4_Medallion-Critique-Beach.pdf`, `S4.4b_Matterbeam.pdf`
- For: §6 critical discussion (trade-offs of layering; data copies/compute cost).
- How: practitioner citations for the "layer count is arbitrary / layering costs compute" counter-argument; cite lightly (blogs, not papers).

**S4.5 [CORE] Marz, N. & Warren, J. (2015): Big Data — Principles and best practices of scalable realtime data systems.** Manning.
- URL: https://www.manning.com/books/big-data (WEB) · free chapter 1 PDF: https://manning-content.s3.amazonaws.com/download/3/4142054-00c8-4115-879e-946c643f3665/big-data-ch01.pdf (OPEN-PDF)
- Filename: `S4.5a_Marz-BigData-Ch1.pdf` (BOOK if you can get it)
- For: §4.1 — the Lambda Architecture definition (batch layer + speed layer + serving layer).
- How: the chapter-1 PDF contains the full lambda principles (immutable data, precompute views) — enough to cite without the whole book.

**S4.6 [CORE] Kreps, J. (2014): Questioning the Lambda Architecture.** O'Reilly Radar.
- URL: https://www.oreilly.com/radar/questioning-the-lambda-architecture/ (WEB)
- Filename: `S4.6_Kreps-Kappa.pdf`
- For: §4.1 — the Kappa argument (why maintaining two code paths for batch+speed is complexity you don't want at 1.1M rows/year).
- How: quote "complexity of maintaining separate batch and speed layers" when justifying batch/micro-batch; pair with S4.7 for the stream-processing worldview.

**S4.7 [CORE] Kreps, J. — Making Sense of Stream Processing (free e-book, O'Reilly/Confluent).**
- URL: https://assets.confluent.io/m/2a60fabedb2dfbb1/original/20190307-EB-Making_Sense_of_Stream_Processing_Confluent.pdf (FREE-REG/OPEN-PDF) (current landing page: https://www.confluent.io/resources/ebook/stream-processing/)
- Filename: `S4.7_Kreps_StreamProcessing.pdf`
- For: §4.1 streaming-vs-batch comparison with proper definitions (event time vs processing time, stream tables).
- How: cite when you characterize what full streaming *would* demand of the platform so your "we deliberately don't need Kafka/Flink here" verdict is informed, not dismissive.

**S4.8 [OPT] Kreps, Narkhede, Rao (2011): Kafka — a Distributed Messaging System for Log Processing.** NetDB'11.
- URL: https://pages.cs.wisc.edu/~akella/CS744/F17/838-CloudPapers/Kafka.pdf (OPEN-PDF)
- Filename: `S4.8_Kafka2011.pdf`
- For: §4.1 when naming the streaming stack you *reject* (Kappa/lambda via Kafka).
- How: one citation when the streaming stack is named; not needed for depth.

**S4.9 [OPT] Apache Flink — Documentation (stateful stream processing).**
- URL: https://nightlies.apache.org/flink/flink-docs-stable/ (WEB) · https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/ (WEB · actual computation model)
- Filename: `S4.9_Flink-Docs.pdf`
- For: §4.1 one line later if the other domain later forces true streaming.
- How: cite exactly once in the outlook sense ("Flink stateful streams") — an informed mention, nothing more.

**S4.10 [CORE] Apache Airflow — Documentation (scheduler, backfill, retries).**
- URL: https://airflow.apache.org/docs/ (WEB) · scheduler internals: https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html
- Filename: `S4.10_Airflow-Docs.pdf`
- For: §4.1 orchestrator choice (DAG-based scheduling, retries, backfill, observability).
- How: quote the backfill/retry paragraph verbatim (schedule + logical date semantics of `data_interval`) so your orchestration description matches actual Airflow behavior when Phase 2 implements it.

**S4.11 [CORE] Dagster — Documentation.**
- URL: https://docs.dagster.io/ (WEB) · https://github.com/dagster-io/dagster
- Filename: `S4.11_Dagster-Docs.pdf`
- For: §4.1 comparison (asset-oriented alternative).
- How: cite Dagster's software-defined-assets philosophy as the rejected paradigm of the comparison; keep symmetric coverage so matrix stays impartial.

**S4.12 [OPT] Prefect — Documentation.**
- URL: https://docs.prefect.io/ (WEB)
- Filename: `S4.12_Prefect-Docs.pdf`
- For: §4.1 comparison row (lightweight, Pythonic flows).
- How: only if you keep a third orchestrator in the table; cron then covers the trivial end of the spectrum.

**S4.13 [OPT] Practitioner comparisons of orchestrators (evidence for the choice).**
- URLs: ZenML: https://www.zenml.io/blog/orchestration-showdown-dagster-vs-prefect-vs-airflow (WEB) · FreeAgent engineering: https://engineering.freeagent.com/2025/05/29/decoding-data-orchestration-tools-comparing-prefect-dagster-airflow-and-mage/ (WEB)
- Filename: `S4.13a_ZenML-Showdown.pdf`, `S4.13b_FreeAgent-Comparison.pdf`
- For: §4.1 "select DAG-based orchestration (Airflow)" — real-world trade-off assessment beyond vendor docs.
- How: cite one when acknowledging the orchestrator wars exist; blogs — one citation max, prefer docs for definitions.

**S4.14 [OPT] An Empirical Study of Developers' Challenges in Implementing Workflows as Code (arXiv, 2024).**
- URL: https://arxiv.org/abs/2406.00180 (WEB)
- Filename: `S4.14_WorkflowsAsCode-Study.pdf`
- For: §4.1 (known Airflow/pipeline-code pain points) and §6 (maintenance risk discussion).
- How: adds an academic counterweight to the practitioner-only docs citations; optional.

**S4.15 [CORE] Christophides, Efthymiou, Stefanidis (2020): End-to-End Entity Resolution for Big Data: A Survey.** *ACM Computing Surveys* 53(2).
- URL: https://arxiv.org/pdf/1905.06397 (OPEN-PDF) · ACM version: https://dl.acm.org/doi/abs/10.1145/3418896
- Filename: `S4.15_EntityResolution_CSUR2020.pdf`
- For: §4.4 cross-snapshot entity resolution (fingerprinting) — *the* academic grounding for the paper's core technique.
- How: draw vocabulary from it (blocking, matching, fusion/consolidation — your `argMax` truth resolution is "consolidation"); position content-fingerprinting as deterministic ER over quasi-identifiers when standard IDs churn.

**S4.16 [OPT] Fellegi & Sunter (1969): A Theory for Record Linkage.** *JASA* 64(328).
- URL: https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049 (PAYWALL)
- Filename: `S4.16_Fellegi-Sunter.pdf`
- For: §4.4 one historical footnote (probabilistic matching vs your deterministic hash).
- How: cite mining-history of matching; mention why *deterministic* hashing fits IDs-with-minor-retimings better than probabilistic matching. Skip if space is tight.

**S4.17 [CORE] Recurring Public Transit Schedules: Stable Identification from GTFS and Similarity Analysis (arXiv 2026, paper id 2606.14713).**
- URL: https://arxiv.org/abs/2606.14713 (OPEN-PDF via `/pdf/` link)
- Filename: `S4.17_Recurring-Schedules-StableID.pdf`
- For: §4.4 — external validation that recurring-schedule identification from GTFS snapshots is a *research problem*, plus related stability analysis techniques.
- How: cite as very recent related work beside your fingerprint approach; contrast their formulation with your `was_corrected`/`snapshot_count` metrics. Copy full author list from the arXiv abstract page while you have wifi.

**S4.18 [CORE] rt2gtfs: correcting public transport timetables with real-time data (arXiv 2026, paper id 2603.11477).**
- URL: https://arxiv.org/abs/2603.11477 (OPEN-PDF via `/pdf/` link)
- Filename: `S4.18_rt2gtfs.pdf`
- For: §4.4.2 continuous real-time extension + §6 outlook (real-time corrections feeding back into schedule truth).
- How: shows live-data → GTFS-timetable correction pipelines exist; supports your "live trip_ids join to snapshot-stable Gold fingerprints via lookup" extension and the Phase-2 outlook. Copy authors from abstract page.

**S4.19 [CORE] Xu, D. et al. (2024/25): Large Language Models for Generative Information Extraction: A Survey.** arXiv 2312.17617; also in *Frontiers of Computer Science* (DOI 10.1007/s11704-024-40555-y).
- URL: https://arxiv.org/abs/2312.17617 (OPEN-PDF) · journal version: https://link.springer.com/article/10.1007/s11704-024-40555-y (PAYWALL — arXiv suffices)
- Filename: `S4.19_Xu_LLM-GenerativeIE.pdf`
- For: §4.4.2 "LLM extraction" — this is the "Xu et al. (2024)" your paper plan lists.
- How: cite the taxonomy of LLM-based IE approaches (prompting/fine-tuning paradigms) when defending multimodal LLM extraction of the 2026 PDF timetables; use it to frame extraction as a research-grade technique, not a hack.

**S4.20 [CORE] Lu, W., Zhang, J., Fan, J. et al. (2025): Large Language Model for Table Processing: A Survey.** arXiv 2402.05121; journal version *Frontiers of Computer Science* (DOI 10.1007/s11704-024-40763-6).
- URL: https://arxiv.org/abs/2402.05121 (OPEN-PDF) · journal version: https://link.springer.com/article/10.1007/s11704-024-40763-6 (PAYWALL — arXiv suffices)
- Filename: `S4.20_Lu_LLM-Table-Processing.pdf`
- For: §4.4.2 — this is the "Lu et al. (2025)" your paper plan lists: LLMs on structured/semi-structured tabular data.
- How: cite for capabilities and failure modes of LLM table extraction — the bridge between "PDF grid" and "mediated by prompt"; both S4.19/S4.20 give you the academic shield for the LLM paragraph.

**S4.21 [CORE] LLMs on Tabular Data — Prediction, Generation, and Understanding: A Survey.** arXiv 2402.17944 (copy the author list from the abstract page while online).
- URL: https://arxiv.org/abs/2402.17944 (OPEN-PDF)
- Filename: `S4.21_LLM-Tabular-Data-Survey.pdf`
- For: §4.4.2/§5 — what LLMs can and cannot do with tabular data (relevant beyond PDFs: ML feature generation context).
- How: cite when stating strengths/limits of LLM table reasoning; author list on abstract page — copy when online.

**S4.22 [CORE] Deep learning for table detection and structure recognition: A Survey.** arXiv 2211.08469.
- URL: https://arxiv.org/pdf/2211.08469 (OPEN-PDF)
- Filename: `S4.22_TableDetectionSurvey.pdf`
- For: §4.4.2 justification why rule-based coordinate PDF-grid parsing fails across the ~65 different timetable layouts (references your preliminary findings).
- How: cite for the layout-diversity problem (table structure recognition is not solved by fixed grid rules); the empirical build-up before your LLM-with-contract solution.

**S4.23 [OPT] Wei et al. (2023): ChatIE — Zero-Shot Information Extraction via Chatting with ChatGPT.** arXiv 2302.10205.
- URL: https://arxiv.org/abs/2302.10205 (OPEN-PDF)
- Filename: `S4.23_ChatIE.pdf`
- For: §4.4.2 — evidence that prompted LLMs perform structured IE zero-shot.
- How: cite alongside Xu survey for the "works without training data" argument (fits: your PDFs have no labeled training set).

**S4.24 [OPT] OmniDocBench — Benchmarking Diverse PDF Document Parsing (arXiv 2412.07626).**
- URL: https://arxiv.org/abs/2412.07626 (OPEN-PDF)
- Filename: `S4.24_OmniDocBench.pdf`
- For: §4.4.2 quantified evidence that heterogeneous-document PDF parsing remains hard even for large models — underlines the need for your deterministic validation contract.
- How: use one sentence ("recent benchmarks still show X% error on realistic document sets — hence per-trip guardrails").

**S4.25 [OPT] Benchmarking Table Extraction from Heterogeneous Scientific PDF Documents (arXiv, 2025/26, id 2511.16134).**
- URL: https://arxiv.org/abs/2511.16134 (OPEN-PDF)
- Filename: `S4.25_HeterogeneousPDF-Tables.pdf`
- For: same paragraph as S4.24 — table-specific benchmark; pick whichever fits better, citing both is overkill.
- How: as above.

**S4.26 [CORE] Hallucination surveys (text + multimodal).**
- URLs: A Survey on Hallucination in LLMs: https://arxiv.org/abs/2311.05232 · Hallucination of Multimodal LLMs: A Survey: https://arxiv.org/abs/2404.18930 (OPEN-PDF each)
- Filename: `S4.26a_LLM-Hallucination-Survey.pdf`, `S4.26b_MLLM-Hallucination-Survey.pdf`
- For: §4.4.2 — the "only behind a deterministic validation contract" argument.
- How: cite for documented hallucination risk in (multimodal) generative extraction → justifying DHID stop-list checks, monotonic stop sequences, time-format validation, per-trip footnote flags. Copy author lists from abstract pages while online.

**S4.27 [CORE] JSON Schema — Specification.**
- URL: https://json-schema.org/specification (WEB)
- Filename: `S4.27_JSON-Schema-Spec.pdf`
- For: §4.4.2 — the concrete standard your extraction output contract ("known DHID stop list, valid time formats…") can reference.
- How: one citation turning "validation contract" from an ad-hoc idea into an industry-standard schema-validation mechanism (per-trip schema validation of LLM output).

**S4.28 [OPT] Generating Structured Outputs from Language Models — JSONSchemaBench (arXiv 2501.10868).**
- URL: https://arxiv.org/abs/2501.10868 (OPEN-PDF)
- Filename: `S4.28_JSONSchemaBench.pdf`
- For: §4.4.2 (constrained decoding / schema-conformant generation — an alternative guardrail to post-hoc validation).
- How: cite when discussing schema-constrained decoding vs validate-and-retry; both belong in the "guardrails" narrative.

**S4.29 [OPT] Great Expectations — Data quality framework docs.**
- URL: https://docs.greatexpectations.io/ (WEB) · https://greatexpectations.io/
- Filename: `S4.29_GreatExpectations.pdf`
- For: §4.4.2 + §6 QA — validator-as-data-asset ("expectation suites") support for your deterministic contract approach.
- How: optional industry citation for declarative validation pipelines; skip if the section gets crowded.

**S4.30 [OPT] Confluent — Schema Registry: Schema Evolution and Compatibility.**
- URL: https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html (WEB)
- Filename: `S4.30_Schema-Evolution.pdf`
- For: §4 resilience-to-schema-drift claim (your 35→42 column APC drift): industry practice for controlled schema evolution (compatibility: backward/forward/full).
- How: one citation when you discuss surviving schema drift without breaking consumers (even if you don't run Kafka — the *compatibility classes* concept is the citable idea).

**S4.31 [OPT] lakeFS — Data reproducibility / Git-for-data articles.**
- URLs: https://lakefs.io/blog/reproducibility/ · https://lakefs.io/blog/git-for-data/ (WEB)
- Filename: `S4.31_lakeFS-Reproducibility.pdf`, `S4.31b_Git-for-Data.pdf`
- For: §4.2 raw-zone immutability & reproducibility argument ("reproduce any past state").
- How: browser-grade citations for immutability/versioning-on-object-storage practice; the FAIR + Kimball citations are stronger backups.

**S4.32 [OPT] DVC-oriented article: Data and Machine Learning Model Versioning with DVC (Towards Data Science).**
- URL: https://towardsdatascience.com/data-and-machine-learning-model-versioning-with-dvc-34fdadd06b15/ (WEB)
- Filename: `S4.32_DVC-Versioning.pdf`
- For: §5 — reproducible Parquet/CSV exports in S3 for reproducible ML training runs (versioned dataset handoff to D3).
- How: optional mention of dataset version control for ML reproducibility; only if you keep a Phase-2 sentence about ML training integrity.

---

### §5 Cross-Domain Data & API Contract (join keys, deliverables, APC quality, external features)

**S5.1 = S2.17 [CORE] DHID / VDV 432 + DELFI ZHV documentation** — see §2 list (S2.17).
- For: §5 ubiquitous spatial join key (`de:09663:*`) bridging GTFS, PDFs, simulation nodes, APC stations.
- How: quote the DHID structure (`de:<community code>:<(stop) ID>` + optional `:Area: quay` suffixes) and use ZHV explanation for the central-stop-register mapping.

**S5.2 [CORE] ClickHouse — HTTP Interface docs.**
- URL: https://clickhouse.com/docs/interfaces/http (WEB)
- Filename: `S5.2_CH-HTTP-Interface.pdf`
- For: §5 delivery interface (read-only SQL access for dashboard/interactive queries without raw DB credentials).
- How: cite for the HTTP query interface as your delivery surface (GET queries, formats=JSON etc.); concrete counterpart to "read-only SQL views".

**S5.3 [OPT] ClickHouse — CREATE VIEW docs.**
- URL: https://clickhouse.com/docs/reference/statements/create/view (WEB)
- Filename: `S5.3_CH-Views.pdf`
- For: §5 exposing Gold as SQL views (normal views = stored SELECT — lightweight access layer to protect underlying tables).
- How: pair with S4.2-conformance sentence: views provide the "read-only" boundary; keep short.

**S5.4 [CORE] TCRP Report 113 (2006): Using Archived AVL-APC Data to Improve Transit Performance and Management.** `Furth, P.G., Hemily, B., Muller, T.H.J., Strathman, J.G.` TRB.
- URL: https://www.trb.org/publications/tcrp/tcrp_rpt_113.pdf (OPEN-PDF)
- Filename: `S5.4_TCRP113_AVL-APC.pdf`
- For: §5 (empirical boarding/dwell distributions for simulation calibration — outputs to D2) + §2 APC assessment + §6 data-quality limitations.
- How: the canonical reference for the *value and pitfalls* of archived AVL/APC data (validation, expansion factors, bias by door type); covers both your D2 calibration exports and quality discussion. Contractor's final report TCRP Web Doc 23 of the same project: https://trb.org/publications/tcrp/tcrp_webdoc_23.pdf — deeper methods chapters.

**S5.5 [OPT] TCQSM — Transit Capacity and Quality of Service Manual (= TCRP Report 100, 2nd ed.).**
- URL: part 0: https://onlinepubs.trb.org/onlinepubs/tcrp/docs/tcrp100/Part0.pdf (OPEN-PDF) · part A: https://onlinepubs.trb.org/onlinepubs/tcrp/tcrp_webdoc_6-a.pdf
- Filename: `S5.5_TCQSM_Part0.pdf`, `S5.5b_TCQSM_PartA.pdf`
- For: §1 motivation (capacity planning) + §5 capacity/utilization KPI definitions for the dashboard (load factors etc.).
- How: cite for standard capacity metrics vocabulary (design load, load factor) instead of improvising KPI definitions; note Part PDFs are large.

**S5.6 [CORE] Automatic Passenger Counter Evaluation: Implications for National Transit Database Reporting.** Transportation Research Record 1835 — Kimpel/Strathman et al.
- URL: https://journals.sagepub.com/doi/10.3141/1835-12 (PAYWALL — fetch via university VPN)
- Filename: `S5.6_TRR1835_APC-Eval.pdf`
- For: §5 + §6 — APC bias and quality filtering (the "APC validation literature (TRR)" your plan lists).
- How: citable evidence that APCs are systematically accurate only if quality flags/gate counts are used — directly relevant to your undocumented `quality_factor` / `passenger_*_measured` field questions to WVV. Verify exact author list/year from the DOI landing page while online.

**S5.7 [CORE] Evaluation of Automatic Passenger Counters.** Transportation Research Record 1308 (1991).
- URL: https://onlinepubs.trb.org/Onlinepubs/trr/1991/1308/1308-010.pdf (OPEN-PDF)
- Filename: `S5.7_TRR1308_APC-Eval-1991.pdf`
- For: §5/§6 — classic APC validation baseline (error rates, boarding/alighting count asymmetries).
- How: as the literature-history anchoring citation; author names printed in the PDF — copy from there when citing.

**S5.8 [CORE] Empirical Study on the Accuracy and Precision of Automatic Passenger Counting in European Bus Services.** Open Transportation Journal, Vol 13 (2019), p.250.
- URL: https://opentransportationjournal.com/VOLUME/13/PAGE/250/FULLTEXT/ (OPEN; if a direct PDF is preferred, try the same path with `/PDF/` instead of `/FULLTEXT/`)
- Filename: `S5.8_APC-European-Bus.pdf`
- For: §6 — European (not US) bus-service APC error magnitudes; closest peer context to WVV's fleet.
- How: cite for realistic error rates in European bus operations — your manual-review queue thresholds can reference this scale; full author list on the PDF.

**S5.9 [OPT] Accuracy of Automatic Passenger Counting in Open Mass Transit Systems.** Open Transportation Journal, Vol 19 (2025).
- URL: https://opentransportationjournal.com/VOLUME/19/ELOCATOR/e26671212383074/PDF/ (OPEN-PDF)
- Filename: `S5.9_APC-OpenMassTransit-2025.pdf`
- For: §6 — up-to-date APC accuracy benchmark (modern sensors).
- How: newer companion to S5.8, shows the error rates persist even with modern counters — good for the risk paragraph.

**S5.10 [CORE] DWD — Climate Data Center (CDC) / Open Data (weather feature source for D3).**
- URLs: https://www.dwd.de/EN/ourservices/cdc/cdc_ueberblick-klimadaten_en.html (WEB) · Open Data server: https://www.dwd.de/EN/ourservices/opendata/opendata.html (WEB)
- Filename: `S5.10_DWD-CDC.pdf`
- For: §5 "From Domain 3: … DWD historical weather data" — cite the concrete planned external feature source for the ML feature tables.
- How: cite the CDC as the canonical German historical-weather archive; mention hourly station observations fit your hourly/stop-event grain.

**S5.11 [OPT] The Impact of Weather on Bus Ridership in Pierce County, Washington.** Journal of Public Transportation (open).
- URL: https://digitalcommons.usf.edu/cgi/viewcontent.cgi?article=1098&context=jpt (OPEN-PDF)
- Filename: `S5.11_WeatherBus-Ridership-JPT.pdf`
- For: §5 — why weather is a meaningful demand feature for the ML feature tables (utilization modeling).
- How: peer-reviewed support that ridership responds significantly to precipitation; citation strength tune-up for weather join. Full authors in the PDF.

**S5.12 [OPT] Extreme-weather and calendar-effects on transit ridership (paywalled exemplars).**
- URLs: https://www.sciencedirect.com/science/article/abs/pii/S1361920924004619 (extreme weather events ↔ US transit ridership) · https://www.sciencedirect.com/science/article/abs/pii/S088677982300408X (calendar events ↔ metro ridership) (PAYWALL)
- Filename: `S5.12a_ExtremeWeather-Ridership.pdf`, `S5.12b_CalendarEvents-Ridership.pdf`
- For: §5 pre-joined calendar/lecture feature tables — peer-reviewed evidence both weather and calendar effects belong in demand models.
- How: one combined citation in §5 ("calendar and weather effects on ridership are well documented…" with both DOIs); fetch via VPN or drop.

**S5.13 [OPT] Predictors of Sustainable Student Mobility in a Suburban Setting.** Sustainability 17(15):6726 (MDPI, open access).
- URL: https://doi.org/10.3390/su17156726 (OPEN)
- Filename: `S5.13_Student-Mobility-Sustainability.pdf`
- For: §5 lecture-calendar context features — empirical university-calendar demand effects.
- How: cite when defending "university lecture intervals" as a first-class demand-context feature for a university city like Würzburg.

**S5.14 = S1.5 Data Mesh (Dehghani)** — see §1 list.
- For: §5 — this is where you use it: domain ownership, data-as-product, self-serve interfaces justify the whole contract chapter.
- How: reference data-product thinking when you enumerate D1 deliverables (per-domain contract = interface as contract between domains).

---

### §6 Critical Discussion & Conclusion (no new sources needed — reuse)

§6 is a discussion chapter and should *cite backwards*:

- **Daily grain vs compact ranges trade-off:** cite Kimball SCD/Type-2 practice (S4.1/S4.2) + MergeTree engine behavior (S3.6) for the compression mitigation.
- **Fingerprint limitations (minute-level retimings → new fingerprint):** cite ER survey (S4.15 — matching granularity), the recurring-schedules paper (S4.17) for the general problem, and your `was_corrected`/`snapshot_count` as mitigation.
- **APC sensor risks:** S5.4–S5.9 (TCRP 113 in particular).
- **Medallion/layering costs (compute duplication):** S4.4 critique blogs, S4.3 accepted-layer definitions.
- **PDF-footnote ambiguity / manual review queue:** S4.22–S4.26 (what models still get wrong), S4.27 (validation contract as the backstop).
- **Schema drift resilience:** S4.30 + Parquet spec (S3.9).
- **Phase-2 transition:** rt2gtfs (S4.18) for the real-time outlook, DEFAS (S2.18) for hub access.

---

## C. Institutional / paywalled sources — campus checklist

| Source | Where | Needed for |
|---|---|---|
| Batini & Scannapieco (2016) | SpringerLink (university VPN) | §1 |
| Kimball & Ross (2013) | Library e-book (Wiley) | §4 |
| Marz & Warren (2015) | Library (Manning) — ch.1 PDF free (see S4.5) | §4 |
| Lu et al. (2025) journal version | Springer FCS (PAYWALL) — arXiv version free | §4 |
| Xu et al. journal version | Springer FCS (PAYWALL) — arXiv version free | §4 |
| TRR 1835 (Kimpel/Strathman) | Sage (PAYWALL) | §5/§6 |
| Fellegi & Sunter (1969) | Taylor & Francis (PAYWALL) — historical footnote (discardable) | §4 |

If you cannot get the paywalled ones in time: the open arXiv/preview/mirror versions and TRB options listed in §B cover every claim — nobody will notice the gaps in a seminar paper.

## D. Reference-management tip

- The two 2026 arXiv finds (S4.17, S4.18) are recent preprints: copy their **exact author lists and venue status from the arXiv abstract pages** while you still have wifi — with your references.bib in mind.
- For every arXiv source you cite, prefer the arXiv IDs as-canonical (`arXiv:2312.17617`) *and* note the journal version if you have it — keeps offline citing honest.
- German-language sources (VDV 432/453/454, ZHV, DEFAS page) are fine to cite as-is; quote translations yourself in the paper when using German material in an English text.
