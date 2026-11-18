# rustfs bucket discovery review & term paper doc

**Session ID:** ses_e12e44aa9ffe1o4wjt2TX09KYK
**Created:** 11/18/2026, 6:22:58 AM
**Updated:** 11/18/2026, 6:44:42 AM

---

## User

@docs/data_pipeline_plan.md check the initial data discovery found here regarding the files in the rustfs bucket. confirm its correctness and add additional information which might be relevant for an initial term paper. create a separate data discovery doc in the docs directory . include references so that I can investigate and reconfirm your findings easily myself. include data examples for the different existing formats

---

## Assistant

I'll verify the claims in the plan against the actual RustFS bucket. Let me first look at the project setup to find how to access the bucket.

---

## Assistant

Both containers are running. Let me get the credentials and check bucket access.

---

## Assistant

The ClickHouse password mismatch noted in the plan is confirmed. Let me find the actual password inside the container:

---

## Assistant

ClickHouse works with `default:default`. Now let me check how ClickHouse is configured for S3 access and list the bucket:

---

## Assistant

ClickHouse has no stored S3 credentials — I'll pass them explicitly in `s3()` calls:

---

## Assistant

S3 access works. Now let me inventory the whole bucket. First, test whether ClickHouse exposes file metadata virtual columns:

---

## Assistant

Virtual columns work. Let me build a small query helper and pull the full bucket inventory:

---

## Assistant

421 objects total. Let me analyze the inventory per prefix and verify each claim in the plan:

---

## Assistant

The Fahrplaene counts look different from the plan — let me look at actual filenames carefully:

---

## Assistant

There are macOS `._*` AppleDouble junk files in the bucket. Let me separate real documents from metadata files:

---

## Assistant

Key findings so far: 201 parquet objects (24 × 598-byte empties ✓), 92 real Fahrplaene docs (61 PDF + 30 XLSX) plus 117 macOS `._*` junk files, no `gtfs/` or `curated/` yet. Now let me verify the parquet details — empty-file lines, row counts per year, schemas:

---

## Assistant

Settings need to go as URL params with HTTP. Let me adjust the helper:

---

## Assistant

Fahrplaene inventory confirmed. Now let me check the local GTFS sample, the existing ClickHouse tables, and the paper docs to align the discovery doc with the term paper:

---

## Assistant

Let me check the repo's scripts and git history for data provenance, and look at the DELFI archive's newest snapshots:

---

## Assistant

Let me identify the likely origins of the context CSVs (holiday APIs) with direct API probes:

---

## Assistant

Found the pedestrian counter dataset. Let me confirm it matches `dataAllStreets.csv`:

---

## Assistant

Let me finish the remaining data checks — overlap duplication, 2026 extra-column null rates, ID uniqueness — and skim the archive doc for PDF/XLSX format details:

---

## Assistant

The volume copy is truncated (erasure-coded). Let me fetch the XLSX via a SigV4 presigned URL generated in bash:

---

## Assistant

The key encoding was wrong (slashes must stay literal in path-style URIs). Fixing:

---

## Assistant

Got the real XLSX (exact object size, `PK` header). Let me inspect its structure:

---

## Assistant

Let me pin down a few final references — the WVV PDF download page, DELFI portal/license, and the OpenHolidays API schema match:

---

## Assistant

One last detail — the `_daily` file date ranges with proper header handling:

---

## Assistant

All verification is complete. Now I'll write the separate data discovery document with the confirmed findings, corrections, data examples, and references:

---

## Assistant

Let me do a final sanity check on the document and the repo state:

---

## Assistant

Done. I verified the initial discovery in `docs/data_pipeline_plan.md` §3 against the live RustFS bucket (via ClickHouse 25.8 `s3()` calls, all reproducible) and wrote the results to a new document: **`docs/data_discovery.md`** (496 lines, untracked — commit when ready).

## What was confirmed
- **Bucket inventory**: 421 objects — `full_api_data/` 201 parquet (1.36 GB), `Additional Data/` 10 CSVs (all 10 row counts match exactly), `Fahrplaene/` 25 line folders with 91 real documents, `gtfs/` and `curated/` don't exist yet, ClickHouse holds only the 9 superseded `wvv.fahrplaene_*` test tables.
- **Schemas**: 142 files × 35 columns, 35 files × 42 columns (2026), 24 empty 598-byte placeholders — and the `null`-typed `is_holiday` breaking parquet schema inference in 2022–2025 reproduces exactly as the plan predicted.
- Plan open questions 2 and 5 are now answered: multi-file line-years are **complementary** halves/quarters (no dedup needed), and 2026 APC data is **partial, ending 2026-04-06**.

## What was corrected (flagged in the doc)
- **Row counts are wrong in the plan**: measured **21,982,494 rows** (2022: 5.79M … 2025: 4.95M, 2026: 1.32M), not ~5.11M — `paper_plan.md` repeats the wrong "5.1M / ~1.1M per year" figure, so this matters for the paper.
- Empty-file lines: 23 & 41 empty in all years, but **24 is empty only 2022–2024** (has data in 2025–26); scattered empties are 2/7/9/25/35/99.
- Fahrplaene split is **61 PDF + 30 XLSX** (plan said ~65/~26); plus **118 macOS `__MACOSX`/`._*` junk files** leaked into the bucket — loaders must filter them.
- `dataAllStreets.csv`: timezone column holds **both `+0100` and `+0200`** (DST), `city` has a leading space; `events_daily` is hourly and extends to 2026-12-31 while `events.csv` ends 2025-12-23.
- New drift detail: `day_type` format changed in 2026 (`K7=8~872` → `01-MD021`), and the 7 new 2026 columns are ~45% NULL.

## What's in the new doc for the term paper
- Per-format **data examples** with real captured rows: parquet (2022 + 2026), comma-CSV, semicolon-CSV (`dataAllStreets.csv`), PDF text excerpt, XLSX internals (single sheet `A1:DB718`, sharedStrings vocabulary), GTFS `stops.txt`/`stop_times.txt`.
- **References to investigate yourself**: DELFI archive listing (verified live — newest snapshot `20251229_…zip`, no `2026/` folder yet; how to read `feed_info.txt` to settle how far it reaches into 2026), WVV PDF-Fahrpläne page, Würzburg open-data portal (`passantenzaehlung-uebersicht-csv` dataset + API call), city event calendar, VDV 432/DHID, TCRP 113 for AVL/APC, Parquet spec — plus pointers into `docs/paper_sources/SOURCES_INDEX.md`.
- A **reproduction appendix** with copy-paste SQL/curl (credentials passed explicitly, never committed; note that reading objects from the docker volume directly doesn't work — use the S3 API).

One heads-up: the plan's claim about a stray character in `clickhouse/.env` did **not** reproduce — the file currently reads exactly `default` and `default:default` authenticates against the running server, so that housekeeping item appears already resolved.
