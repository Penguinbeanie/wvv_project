-- 03_schema.sql — ClickHouse DDL for the WVV Fahrplaene test ingestion.
-- Applied over the HTTP interface by 04_load_clickhouse.sh.

CREATE DATABASE IF NOT EXISTS wvv;

CREATE TABLE IF NOT EXISTS wvv.fahrplaene_documents
(
    pdf_name    String,
    title       String,
    doc_type    String,
    lines       String,
    valid_from  Nullable(Date),
    valid_until Nullable(Date),
    stand       Nullable(Date),
    pages       UInt32,
    source_dir  String,
    extracted_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY pdf_name;

CREATE TABLE IF NOT EXISTS wvv.fahrplaene_raw_pages
(
    pdf_name     String,
    page         UInt32,
    text         String,
    extracted_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (pdf_name, page);

CREATE TABLE IF NOT EXISTS wvv.fahrplaene_departures
(
    pdf_name       String,
    line           String,
    direction      String,
    day_type       String,
    stop           String,
    departure_time String,
    notes          String,
    extracted_at   DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (pdf_name, line, stop, departure_time);

CREATE TABLE IF NOT EXISTS wvv.fahrplaene_footnotes
(
    pdf_name     String,
    code         String,
    description  String,
    extracted_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (pdf_name, code);

-- coordinate-based grid extraction (02b_parse_grids.py, PyMuPDF)
CREATE TABLE IF NOT EXISTS wvv.fahrplaene_grid_departures
(
    pdf_name       String,
    page           UInt32,
    line           String,
    direction      String,   -- normalized destination (last region after the final dash)
    route          String,   -- full route string as printed, for reference
    day_type       String,
    trip_id        String,   -- p<page>b<block>c<column>; estimated gap-fills use ...e<k>
    stop           String,
    stop_seq       UInt32,
    departure_time String,
    estimated      UInt8,    -- 1 = interpolated from "usw." gap, not printed in the PDF
    notes          String,
    valid_from     Nullable(Date),
    valid_until    Nullable(Date),
    extracted_at   DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (pdf_name, page, trip_id, stop_seq);

CREATE TABLE IF NOT EXISTS wvv.fahrplaene_trips
(
    pdf_name     String,
    page         UInt32,
    line         String,
    direction    String,   -- normalized destination
    route        String,   -- full route string as printed
    day_type     String,
    trip_id      String,
    first_stop   String,
    last_stop    String,
    first_time   String,
    last_time    String,
    stops_served UInt32,
    valid_from   Nullable(Date),
    valid_until  Nullable(Date),
    extracted_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (pdf_name, page, trip_id);

-- per document x line validity window (05_validity.py)
CREATE TABLE IF NOT EXISTS wvv.fahrplaene_document_validity
(
    pdf_name    String,
    line        String,
    valid_from  Nullable(Date),
    valid_until Nullable(Date),
    extracted_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (pdf_name, line);

-- routes dimension: line + direction + start/end stop (06_routes.py),
-- for cross-referencing headers missing in newly parsed documents
CREATE TABLE IF NOT EXISTS wvv.fahrplaene_routes
(
    line             String,
    direction        String,
    start_stop       String,
    end_stop         String,
    n_trips          UInt32,
    n_documents      UInt32,
    first_valid_from Nullable(Date),
    last_valid_until Nullable(Date),
    extracted_at     DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (line, direction);
