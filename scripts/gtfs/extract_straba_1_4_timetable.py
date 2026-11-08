#!/usr/bin/env python3
"""Extract full timetables for WVV Straba lines 1 and 4 from a DELFI GTFS feed.

Reads a GTFS directory, selects tram routes by route_short_name (agency 13346,
route_type 0), resolves which trips run on which dates in a target window via
calendar.txt + calendar_dates.txt, and renders a markdown timetable grouped by
line / direction / service pattern (day type).

Usage:
    python3 extract_straba_1_4_timetable.py <gtfs_dir> <output_md>
"""
import csv
import sys
import os
from collections import defaultdict
from datetime import date, timedelta

# 29.07.2023 - 11.09.2023 (Bavarian summer holidays timetable)
WINDOW_START = date(2023, 7, 29)
WINDOW_END = date(2023, 9, 11)
AGENCY_ID = "13346"          # Wuerzburger Strassenbahn
ROUTE_TYPE_TRAM = "0"
LINE_SHORT_NAMES = {"1", "4"}


def parse_date_int(yyyymmdd):
    s = str(yyyymmdd)
    return date(int(s[0:4]), int(s[4:6]), int(s[6:8]))


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def hhmm(t):
    """'8:02:00' or '08:02:00' -> '8:02'; keep hours >= 24 as-is."""
    if not t:
        return ""
    parts = t.split(":")
    h = int(parts[0])
    return f"{h}:{parts[1]}"


def daterange(d0, d1):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=1)


def compact_ranges(dates):
    """Sort a list of dates into 'dd.mm.' ranges plus isolated days."""
    ds = sorted(dates)
    out = []
    i = 0
    while i < len(ds):
        j = i
        while j + 1 < len(ds) and ds[j + 1] == ds[j] + timedelta(days=1):
            j += 1
        if j > i + 1:
            out.append(f"{ds[i].strftime('%d.%m.')}\u2013{ds[j].strftime('%d.%m.%Y')}")
        elif j == i + 1:
            out.append(f"{ds[i].strftime('%d.%m.')}, {ds[j].strftime('%d.%m.%Y')}")
        else:
            out.append(ds[i].strftime("%d.%m.%Y"))
        i = j + 1
    return "; ".join(out)


def main():
    gtfs_dir = sys.argv[1]
    out_path = sys.argv[2]

    # --- routes: tram routes of agency 13346 with the wanted short names ---
    wanted_route_ids = {}
    for r in read_csv(os.path.join(gtfs_dir, "routes.txt")):
        if (r["agency_id"] == AGENCY_ID and r["route_type"] == ROUTE_TYPE_TRAM
                and r["route_short_name"] in LINE_SHORT_NAMES):
            wanted_route_ids[r["route_id"]] = r["route_short_name"]
    if not wanted_route_ids:
        sys.exit("No matching tram routes found")

    # --- trips of those routes ---
    trips = {}  # trip_id -> dict(route, service, headsign, direction)
    for t in read_csv(os.path.join(gtfs_dir, "trips.txt")):
        if t["route_id"] in wanted_route_ids:
            trips[t["trip_id"]] = {
                "line": wanted_route_ids[t["route_id"]],
                "service": t["service_id"],
                "headsign": t.get("trip_headsign", ""),
                "direction": t.get("direction_id", "0"),
            }
    print(f"trips: {len(trips)}")

    # --- calendar (base weekday patterns) ---
    base = {}  # service_id -> (weekday_flags, start, end)
    for c in read_csv(os.path.join(gtfs_dir, "calendar.txt")):
        base[c["service_id"]] = (
            [c["monday"], c["tuesday"], c["wednesday"], c["thursday"],
             c["friday"], c["saturday"], c["sunday"]],
            parse_date_int(c["start_date"]), parse_date_int(c["end_date"]),
        )

    # --- calendar_dates exceptions (only for our services) ---
    add = defaultdict(set)
    rem = defaultdict(set)
    with open(os.path.join(gtfs_dir, "calendar_dates.txt"), newline="",
              encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for cd in reader:
            sid = cd["service_id"]
            if sid in base or sid in {t["service"] for t in trips.values()}:
                d = parse_date_int(cd["date"])
                if cd["exception_type"] == "1":
                    add[sid].add(d)
                elif cd["exception_type"] == "2":
                    rem[sid].add(d)

    # --- active dates per service within the window ---
    window = list(daterange(WINDOW_START, WINDOW_END))
    service_dates = defaultdict(set)  # service_id -> set of dates in window
    for sid in {t["service"] for t in trips.values()}:
        dates = set()
        weekdays, start, end = base[sid]  # KeyError would mean missing service
        for d in window:
            if start <= d <= end and weekdays[d.weekday()] == "1":
                dates.add(d)
        dates |= add[sid] & set(window)
        dates -= rem[sid]
        service_dates[sid] = dates

    # --- trip -> dates ---
    trip_dates = {tid: service_dates[t["service"]] for tid, t in trips.items()}
    with_service = {tid for tid, ds in trip_dates.items() if ds}
    merged_dates = set().union(*trip_dates.values()) if trip_dates else set()
    uncovered = [d for d in window if d not in merged_dates]
    print(f"trips active in window: {len(with_service)}")
    print(f"dates in window covered: {len(set(window) & merged_dates)}")
    if uncovered:
        print("NOT covered by feed: " + ", ".join(d.isoformat() for d in uncovered))

    # --- stop_times: single pass, keep rows of wanted trips ---
    # Fast path: trip_id is the first CSV field and never contains a comma.
    stop_times = defaultdict(list)  # trip_id -> [(stop_seq, stop_id, dep_time)]
    with open(os.path.join(gtfs_dir, "stop_times.txt"), encoding="utf-8") as f:
        header = f.readline()
        for line in f:
            tid, _rest = (line.split(",", 1) + [""])[:2]
            tid = tid.strip().strip('"')
            if tid in trips:
                cols = line.rstrip("\r\n").split(",")
                stop_times[tid].append((int(cols[4]), cols[3].strip('"'), cols[2]))

    # --- stop names ---
    stop_ids_used = {sid for rows in stop_times.values() for _, sid, _ in rows}
    stop_names = {}
    with open(os.path.join(gtfs_dir, "stops.txt"), newline="", encoding="utf-8") as f:
        for s in csv.DictReader(f):
            if s["stop_id"] in stop_ids_used:
                stop_names[s["stop_id"]] = s["stop_name"]

    # --- cluster dates by identical active-trip-set, per (line, direction) ---
    # All trips in such a cluster run on every date of the cluster, so each
    # cluster table is a complete day-type timetable (like a PDF grid column
    # block: Mo-Fr / Sa / So+Feiertag) with no per-trip exceptions.
    wd = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    trips_per_dir_date = defaultdict(dict)  # (line, direction) -> date -> set(trip)
    for tid, ds in trip_dates.items():
        if not ds:
            continue
        t = trips[tid]
        for d in ds:
            trips_per_dir_date[(t["line"], t["direction"])].setdefault(d, set()).add(tid)

    clusters = defaultdict(lambda: defaultdict(list))  # (line, dir) -> trip-set -> [dates]
    for key, by_date in trips_per_dir_date.items():
        for d in window:
            pattern = frozenset(by_date.get(d, ()))
            clusters[key][pattern].append(d)

    lines = []
    lines.append("# Straba Linien 1 und 4 \u2014 Fahrplan "
                 f"{WINDOW_START.strftime('%d.%m.%Y')}\u2013{WINDOW_END.strftime('%d.%m.%Y')}")
    lines.append("")
    lines.append(f"*Quelle: DELFI-GTFS-Snapshot `{os.path.basename(gtfs_dir)}` "
                 "(Agentur 13346 \u201eW\u00fcrzburger Stra\u00dfenbahn\u201c, Stra\u00dfenbahn "
                 "route_type 0). Generiert mit "
                 "`scripts/gtfs/extract_straba_1_4_timetable.py`.*")
    lines.append("")
    lines.append(f"*Geltungsbereich laut Feed: "
                 f"{min(merged_dates).strftime('%d.%m.%Y')}\u2013"
                 f"{max(merged_dates).strftime('%d.%m.%Y')}."
                 + ("" if not uncovered else
                    " Achtung: **29.07. und 30.07.2023 sind in diesem Feed nicht "
                    "enthalten** \u2014 der Sommerfahrplan beginnt laut GTFS erst am "
                    "31.07.2023; f\u00fcr diese beiden Tage gilt der vorherige Fahrplan, "
                    "der in diesem Snapshot nicht enthalten ist.*"))
    lines.append("")

    # overview table: what runs on which day types per line/direction
    lines.append("## \u00dcbersicht")
    lines.append("")
    lines.append("| Linie | Richtung | Tagestyp | Verkehrstage | Fahrten |")
    lines.append("|---|---|---|---|---|")

    def daytype_label(dates):
        wds = sorted({d.weekday() for d in dates})
        names = [wd[w] for w in wds]
        if wds == list(range(5)):
            return "Mo\u2013Fr"
        if wds == list(range(6)):
            return "Mo\u2013Sa"
        # Sundays plus isolated weekday holidays (e.g. 15.08. Mari\u00e4 Himmelfahrt)
        if wds == [5, 6] or (6 in wds and any(w < 5 for w in wds)
                             and not all(w in wds for w in range(5))):
            extra = [d for d in sorted(dates) if d.weekday() < 5]
            lbl = "So/Feiertage"
            if extra:
                lbl += " (Feiertag: " + ", ".join(
                    d.strftime("%d.%m.") for d in extra) + ")"
            return lbl
        if wds == [5]:
            return "Sa"
        if wds == [6]:
            return "So"
        if len(names) > 1:
            return f"{names[0]}\u2013{names[-1]}"
        return names[0]

    lines.append("## Hinweise")
    lines.append("")
    lines.append("- **24:xx / 25:xx-Uhrzeiten** folgen der GTFS-Konvention: sie beziehen "
                 "sich auf den *Betriebstag* und bedeuten 0:xx/1:xx Uhr des "
                 " Folgetags (z.\u00a0B. f\u00e4hrt die Freitags-Fahrt 24:03 Uhr am "
                 "Samstag um 0:03 Uhr). PDF-Fahrpl\u00e4ne zeigen daf\u00fcr meist 0:03.")
    lines.append("- **Mehrfach vorkommende Haltestellennamen** sind verschiedene "
                 "Haltestellen (z.\u00a0B. Juliuspromenade auf beiden Stra\u00dfenseiten "
                 "bei Linie 4 \u00fcber Hauptbahnhof West) \u2014 nicht dieselbe Spalte.")
    lines.append("- Kurzfahrten enden/beginnen au\u00dferhalb der Endstation; fehlende "
                 "Zeiten sind mit \u2013 markiert.")
    lines.append("")
    line_dirs = sorted(clusters.keys(), key=lambda k: (k[0], k[1]))
    for key in line_dirs:
        line_no, direction = key
        for pattern, dates in sorted(clusters[key].items(),
                                     key=lambda kv: (min(kv[1]))):
            if not pattern:
                continue
            d_sorted = sorted(dates)
            direction_name = "??"
            # terminus label from the cluster's longest trip
            longest = max(pattern, key=lambda t: len(stop_times.get(t) or []))
            if stop_times.get(longest):
                last_sid = sorted(stop_times[longest])[-1][1]
                direction_name = stop_names.get(last_sid, last_sid)
            lines.append(f"| {line_no} | {direction} \u2192 {direction_name} | "
                         f"{daytype_label(d_sorted)} | {compact_ranges(d_sorted)} "
                         f"| {len(pattern)} |")
    lines.append("")

    # timetable per (line, direction, date-cluster)
    for key in line_dirs:
        line_no, direction = key
        for pattern, dates in sorted(clusters[key].items(),
                                    key=lambda kv: (min(kv[1]))):
            if not pattern:
                continue
            d_sorted = sorted(dates)
            tids = list(pattern)
            # stop order via the cluster's longest trip
            longest = max(tids, key=lambda t: len(stop_times.get(t) or []))
            stop_order = [sid for _, sid, _ in sorted(stop_times[longest])]
            first_stop = stop_names.get(stop_order[0], stop_order[0])
            last_stop = stop_names.get(stop_order[-1], stop_order[-1])

            def first_dep(tid):
                st = stop_times.get(tid) or [("", "", "999:99:99")]
                h, m, s = st[0][2].split(":")
                return f"{int(h):02d}:{m}:{s}"
            tids_sorted = sorted(tids, key=first_dep)

            lines.append(f"## Linie {line_no} \u2192 {last_stop} "
                         f"({daytype_label(d_sorted)}, "
                         f"{compact_ranges(d_sorted)})")
            lines.append("")
            lines.append(f"{len(tids_sorted)} Fahrten von **{first_stop}** "
                         f"nach **{last_stop}** "
                         f"(an {len(d_sorted)} Tagen: {compact_ranges(d_sorted)}).")
            lines.append("")
            header = ["Abfahrt " + first_stop]
            header += [stop_names.get(s, s) for s in stop_order[1:-1]]
            header += ["Ankunft " + last_stop]
            lines.append("| # | " + " | ".join(header) + " |")
            lines.append("|---" * (len(header) + 1) + "|")
            for n, tid in enumerate(tids_sorted, 1):
                times = {sid: dep for _, sid, dep in stop_times[tid]}
                row = [str(n)]
                for sid in stop_order:
                    dep = times.get(sid, "")
                    row.append(hhmm(dep) if dep else "\u2013")
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"written: {out_path} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
