# GTFS-Datenmodell: Bronze → Silver → Gold

Datenmodell für die DELFI-GTFS-Snapshots (alle Wochensnapshots ab 2022) aus
dem Archiv `https://archiv.opendata-oepnv.de/DELFI/Soll-Fahrplandaten (GTFS)/`
als Ersatz für die PDF-basierte Fahrplan-Extraktion. Ziel: SOLL-Daten des WVV
(Würzburg) als einheitliche, versionierte Tabellen in ClickHouse für Simulation
und Modelltraining.

Validierung (Sommer-Baustelle 2023, Straba 1/4 + SEV): Trip-umper-Trip-Vergleich
gegen den PDF-Baustellenfahrplan ergab 100% Übereinstimmung — der Feed enthält
auch Baustellenfahrpläne und Schienenersatzverkehr und ist als Ground Truth für
Soll-Daten geeignet. Details siehe Session-Unterlagen.

## Grundprinzipien

1. **Stabile vs. snapshot-lokale IDs.** `stop_id` (DHID, `de:09663:...`) und
   `agency_id` sind über alle Snapshots stabil. `route_id`, `trip_id` und
   `service_id` sind opak und ändern sich **jeden Export** (z. B. Linie 1:
   `5316210_0` im Snapshot 2023-08-14 vs. `de:nvm:stwü|Straba|1:_0` in 2025).
   Joins über Snapshots hinweg daher nur über stabile IDs oder
   inhaltsbasierte Fingerprints, nie über GTFS-Roh-IDs.
2. **Referenzdaten = SCD-artig per Append.** Stops/Routen ändern sich langsam.
   Es gibt kein UPDATE/DELETE: jede Änderung ist eine neue Zeile mit neuem
   `snapshot_date`. Der aktuelle Zustand ist `argMax(...)` je Attribut, der
   Lebenszyklus ist `first_seen`/`last_seen`. Eine Haltestelle, die aus dem
   Feed verschwindet (z. B. Baustellen-Sonderhalt nach Ende der Baustelle),
   ist per `last_seen < max(snapshot_date)` inaktiv — nie löschen.
3. **Kalenderauflösung genau einmal.** `calendar.txt` + `calendar_dates.txt`
   werden pro Snapshot zu konkreten Servicetagen aufgelöst
   (`silver_service_dates`). Alles downstream rechnet nur noch mit Daten.
4. **Silver = verlustfreie Evidenz** (jede Trip-Tag-Beobachtung aus jedem
   Snapshot), **Gold = effektive Wahrheit** (eine Zeile je Trip-Tag, Features
   materialisiert). Gold ist immer aus Silver rekonstruierbar (INSERT … SELECT,
   nie manuell gepflegt).
5. **GTFS-Tageszeiten.** Zeiten über Mitternacht werden im Betriebstag-Format
   geführt (24:03 = 1443 Minuten). Stunden sind teilweise ungepolstert
   (`6:29:00`), `feed_info.txt` fehlt in manchen Snapshots (Metadaten dann aus
   der Beschreibungs-PDF), Zeilen sind CRLF, Felder quoted/unquoted gemischt.

## Ebenen-Übersicht

| Ebene | Granulat | Zweck |
|---|---|---|
| Zip-Archiv (Platte) | Snapshot-Original | unveränderte Rohquelle |
| `meta_snapshot` | Snapshot | Registry, Validität, Integritätschecks |
| bronze_* | Rohzeile + `snapshot_date` | 1:1 mit GTFS-Dateien |
| silver_* (Stops, Routen, Trips, Servicetage) | aufgelöst je Snapshot | Versionierte Evidenz |
| `silver_trip_day` | (Snapshot, Fingerprint, Servicedatum) | Grundkorn der Evidenz |
| `gold_trip_day` | (Fingerprint, Servicedatum) | effektive Wahrheit + Features |
| `gold_stop`, `gold_line` | stabile ID | effektive Stamm- und Lebenszyklusdaten |
| `ref_calendar` | Kalendertag | bayerische Feier-/Schulferientage (extern) |
| `v_*` (Views) | abgeleitet | Gültigkeitsbereiche, Tagtypen, Auswertungen |

## DDL (ClickHouse)

### Metadaten

```sql
CREATE TABLE meta_snapshot (
    snapshot_date   Date,
    source_url      String,
    sha256_zip      String,
    valid_from      Nullable(Date),   -- feed_info / Beschreibungs-PDF
    valid_to        Nullable(Date),
    wvv_trip_count  UInt32,           -- Integritätscheck: Trips Agentur 13346
    notes           String,           -- DELFI-Hinweis "auslaufende Daten"
    ingested_at     DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree ORDER BY snapshot_date;
```

Der Integritätscheck pro Snapshot umfasst mindestens: alle 5 Straba-Linien
vorhanden (Fehlerbild: Snapshot 2025 hatte nur Linien 1/4/5), Trip-Zahl je
Linie/Richtung/Tagtyp plausibel (keine Taglöcher), Endpunkte konsistent,
Stop-IDs im Raum Würzburg (`de:09663:`, `de:09679:`).

### Bronze (Roh; eine Tabelle je GTFS-Datei)

```sql
CREATE TABLE bronze_agency (
    snapshot_date Date, agency_id String, agency_name String,
    agency_url String, agency_timezone String
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, agency_id);

CREATE TABLE bronze_routes (
    snapshot_date Date, route_id String, agency_id String,
    route_short_name String, route_type UInt8,
    route_long_name String, route_color String, route_text_color String
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, route_id);

CREATE TABLE bronze_trips (
    snapshot_date Date, route_id String, service_id String,
    trip_id String, trip_headsign String, direction_id UInt8,
    block_id Nullable(String), shape_id Nullable(String)
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, trip_id);

CREATE TABLE bronze_stops (
    snapshot_date Date, stop_id String, stop_name String,
    lat Float64, lon Float64, location_type UInt8,
    parent_station Nullable(String), platform_code Nullable(String)
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, stop_id);

CREATE TABLE bronze_stop_times (
    snapshot_date Date, trip_id String, stop_sequence UInt32,
    stop_id String, arrival_min Int32, departure_min Int32,   -- Betriebstag-Minuten
    pickup_type UInt8, drop_off_type UInt8, stop_headsign String
) ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(snapshot_date)
ORDER BY (snapshot_date, trip_id, stop_sequence);

CREATE TABLE bronze_calendar (
    snapshot_date Date, service_id String,
    monday UInt8, tuesday UInt8, wednesday UInt8, thursday UInt8,
    friday UInt8, saturday UInt8, sunday UInt8,
    start_date Date, end_date Date
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, service_id);

CREATE TABLE bronze_calendar_dates (
    snapshot_date Date, service_id String, exception_date Date,
    exception_type UInt8   -- 1 = ADD, 2 = REMOVE
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, service_id, exception_date);
```

`shapes`, `pathways`, `transfers`, `frequencies`: nicht laden, solange kein
Bedarf (shapes allein ~330 MB je Snapshot); sollte Bedarf entstehen, nur
bereichsbezogen nach WVV-Routen gefiltert.

### Silver (aufgelöst und versioniert)

```sql
-- Kalender je Snapshot einmalig auflösen
CREATE TABLE silver_service_dates (
    snapshot_date Date,
    service_id    String,
    service_date  Date
) ENGINE = MergeTree ORDER BY (service_id, service_date, snapshot_date);
-- aus bronze_calendar (Wochentagsmaske ∩ [start_date, end_date])
-- vereinigt mit bronze_calendar_dates (ADD), minus REMOVE

-- Trip mit inhaltsbasiertem Fingerprint
CREATE TABLE silver_trip (
    snapshot_date Date,
    trip_id       String,
    fingerprint   UInt64,   -- cityHash64(line, direction, stop_ids, dep_minutes)
    line          LowCardinality(String),
    direction     Enum8('0' = 0, '1' = 1),
    block_id      String,
    service_id    String,
    stop_ids      Array(String),
    dep_minutes   Array(Int32)
) ENGINE = ReplacingMergeTree ORDER BY (snapshot_date, trip_id);

-- Haltestellen-Historie (keine Updates, nur Appends)
CREATE TABLE silver_stop (
    snapshot_date  Date,
    stop_id        String,        -- DHID: stabil über alle Snapshots
    stop_name      String,
    lat            Float64, lon Float64,
    parent_station String,
    location_type  UInt8,
    platform_code  String
) ENGINE = MergeTree ORDER BY (stop_id, snapshot_date);

-- Granulat der Evidenz
CREATE TABLE silver_trip_day (
    snapshot_date Date,
    fingerprint   UInt64,
    service_date  Date
) ENGINE = MergeTree PARTITION BY toYYYYMM(service_date)
ORDER BY (fingerprint, service_date, snapshot_date);
```

### Gold (effektive Wahrheit + Features)

```sql
CREATE TABLE gold_trip_day (
    fingerprint       UInt64,
    service_date      Date,
    line              LowCardinality(String),
    direction         Enum8('0' = 0, '1' = 1),
    stop_ids          Array(String),
    dep_minutes       Array(Int32),
    block_id          String,
    weekday           UInt8,     -- 1 = Mo ... 7 = So
    is_public_holiday UInt8,     -- Feiertag Bayern (inkl. 15.08.)
    is_school_holiday UInt8,     -- bayerische Ferien
    pattern_id        UInt64,    -- cityHash64(zeiliges trip-set des Tagtyps)
    snapshot_count    UInt16,    -- wieviele Snapshots belegen diesen Trip-Tag
    first_seen        Date,      -- frühester beobachtender Snapshot
    last_seen         Date,
    was_corrected     UInt8      -- Zeiten wichen zwischen Snapshots ab
) ENGINE = ReplacingMergeTree ORDER BY (fingerprint, service_date);

CREATE TABLE gold_stop (
    stop_id        String,
    stop_name      String,
    lat            Float64, lon Float64,
    parent_station String,
    platform_code  String,
    first_seen     Date,
    last_seen      Date,
    is_active      UInt8      -- last_seen = letzter Snapshot im Register
) ENGINE = ReplacingMergeTree ORDER BY stop_id;

-- optional, analog: gold_line (line, agency_id, first_seen, last_seen)

CREATE TABLE ref_calendar (
    service_date      Date,
    weekday           UInt8,
    is_public_holiday UInt8,
    is_school_holiday UInt8,
    holiday_name      LowCardinality(String)
) ENGINE = MergeTree ORDER BY service_date;
-- extern: Feiertage + Schulferien Bayern; einzige Tabelle, die
-- nicht aus dem Feed stammt. Wichtigste Feature-Quelle, da sich das
-- WVV-Betriebsmuster nach genau diesen Flags richtet (15.08. wie So/Feiertag).
```

### Views (abgeleitet, nie primär)

```sql
-- lesbares "Fahrplanblock"-Format (gueltig von-bis je Tagtyp), rebuild aus Gold:
-- je (line, direction, weekday-Muster) Gruppenbildung der service_dates,
-- Lückenschluss über Tagtyp-spezifische Schrittweite, Split bei Lücken
-- (gleiche compact_ranges-Logik wie im Extractor-Skript).
CREATE VIEW v_timetable_range AS ...
```

## Merge-Semantik (silver → gold)

- **Dedup:** ein physischer Trip steckt in ~10–20 aufeinanderfolgenden
  Snapshots; Korn `(fingerprint, service_date)` dedupliziert das.
- **Effektive Version:** `argMax(..., snapshot_date)` — eine Korrektur, die
  mittig veröffentlicht wurde, überschreibt die Erstveröffentlichung; die
  Erstveröffentlichung bleibt in silver erhalten ( Audit).
- **Konflikte:** `was_corrected` markiert Trip-Tage mit abweichenden Zeiten;
  für Training auffälliger Tage filterbar.
- **Vertrauen:** `snapshot_count` als freies Konfidenzmaß (Konsens über
  Snapshots ersetzt den PDF-Abgleich).

## Nächste Schritte

1. Ingest-Skript (`scripts/gtfs/01_ingest_snapshot.py`): Zip → Entpacken →
   WVV-Filter (Agentur 13346; Haltestellenraum `de:09663`/`de:09679`) → bronze (HTTP-Interface wie bestehender Loader).
2. Transform-SQL (`scripts/gtfs/03_transform.sql`): silver und gold wie oben.
3. Range-View und Tagtyp-Clustering in SQL (`arrayJoin`, `groupArray`).
