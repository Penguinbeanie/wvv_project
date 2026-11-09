#!/usr/bin/env python3
"""Placeholder — 2026 Fahrplan PDF extraction (plan: docs/data_pipeline_plan.md §5.3).

Process per 2026-valid PDF from the RustFS bucket (wvv/Fahrplaene/):

  1. PyMuPDF: extract the layout text of each page and rasterize the page to PNG
     (~150–200 dpi). Text extraction and rasterization only — no grid parsing, no OCR.
  2. Send text + image of each page to DeepSeek v4.1 flash, with a fixed extraction
     contract in the prompt: the schedule CSV schema, the line list (numbers/names from
     the GTFS line dimension), and the known WVV stop names for normalization.
  3. Validate the returned data in deterministic glue code (time format, stop-name
     resolution, monotone trips, day types); failures go to a review queue —
     nothing is loaded unvalidated.
  4. Write the validated CSVs to wvv/curated/schedules_2026/ and load them into the
     ClickHouse schedule layer (bronze -> silver -> gold) as a pseudo-snapshot with
     source = 'pdf'.

The superseded grid-parsing pipeline of the initial approach was removed; its
documentation is preserved in docs/archive/.
"""
