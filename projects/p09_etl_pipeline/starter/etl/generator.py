"""Deterministic generator for messy raw bike-share files.

Each day gets one trip file, alternating CSV (naive local timestamps) and JSON Lines (ISO-8601 with UTC offset).
Every file deliberately contains problems a real feed has:

* one exact duplicate row,
* one row with an unparseable timestamp,
* one row with an unknown station id (``S99``),
* one row whose end time is before its start time,
* from the second day on, two late-arriving trips that started early on the previous day,
* from the third day on, a re-delivery of a trip already sent in an earlier file.

Station snapshots are written on the first day and on day four, where one station is renamed, one changes capacity,
and a new station opens. That drives the SCD type 2 history in ``dim_station``.
"""

import csv
import json
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from etl.models import LOCAL_TZ, TRIP_FIELDS, Station

BASE_STATIONS: tuple[Station, ...] = (
    Station("S01", "Union Square", 30),
    Station("S02", "City Hall", 24),
    Station("S03", "Harbor Point", 20),
    Station("S04", "Museum Mile", 18),
    Station("S05", "Central Station", 40),
    Station("S06", "Riverside Park", 22),
    Station("S07", "University Ave", 26),
    Station("S08", "Market Street", 28),
)
"""Stations in the first snapshot."""

CHANGE_DAY_INDEX = 3
"""Zero-based day on which the second station snapshot (rename, capacity change, new station) is published."""

UNKNOWN_STATION = "S99"


@dataclass(frozen=True, slots=True)
class GeneratedFiles:
    """Paths written by :func:`generate`.

    Attributes:
        trip_files: One trip file per day, in date order.
        station_files: Station snapshots, in date order.
    """

    trip_files: list[Path]
    station_files: list[Path]


def stations_on(day_index: int) -> list[Station]:
    """Return the station snapshot that is current on a given day.

    Args:
        day_index: Zero-based day number.

    Returns:
        The stations in effect on that day.
    """
    if day_index < CHANGE_DAY_INDEX:
        return list(BASE_STATIONS)
    changed = {
        "S03": Station("S03", "Harbor Point Plaza", 20),
        "S07": Station("S07", "University Ave", 32),
    }
    return [changed.get(s.station_id, s) for s in BASE_STATIONS] + [Station("S09", "Ferry Terminal", 16)]


def _format(moment: datetime, as_json: bool) -> str:
    if as_json:
        return moment.isoformat()
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def _trip(
    rng: random.Random, trip_id: str, day: date, stations: list[Station], as_json: bool, *, early: bool = False
) -> dict[str, str]:
    window = 3 * 60 if early else 15 * 60
    start = datetime(day.year, day.month, day.day, 6, tzinfo=LOCAL_TZ) + timedelta(minutes=rng.randrange(0, window))
    end = start + timedelta(minutes=rng.randint(3, 60), seconds=rng.randrange(60))
    a, b = rng.sample(stations, 2)
    return {
        "trip_id": trip_id,
        "start_time": _format(start, as_json),
        "end_time": _format(end, as_json),
        "start_station_id": a.station_id,
        "end_station_id": b.station_id,
        "bike_id": f"B{rng.randrange(100, 160)}",
        "member_type": rng.choice(["member", "member", "casual"]),
    }


def _write_trips(path: Path, rows: list[dict[str, str]]) -> None:
    if path.suffix == ".jsonl":
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(TRIP_FIELDS))
        writer.writeheader()
        writer.writerows(rows)


def write_stations(path: Path, stations: list[Station]) -> Path:
    """Write a station snapshot CSV.

    Args:
        path: Destination file.
        stations: Stations to write.

    Returns:
        ``path``.
    """
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["station_id", "name", "capacity"])
        for s in stations:
            writer.writerow([s.station_id, s.name, s.capacity])
    return path


def generate(
    raw_dir: Path,
    *,
    start: date = date(2026, 3, 5),
    days: int = 7,
    trips_per_day: int = 30,
    seed: int = 9,
) -> GeneratedFiles:
    """Write raw trip and station files into ``raw_dir``.

    The same arguments always produce byte-identical files. The default range crosses the US daylight-saving switch
    on 2026-03-08, so UTC offsets change mid-week.

    Args:
        raw_dir: Directory to write into (created if missing).
        start: First day.
        days: Number of daily trip files.
        trips_per_day: Clean trips per day (problem rows are added on top).
        seed: Random seed.

    Returns:
        The written file paths.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    station_files = [write_stations(raw_dir / f"stations_{start.isoformat()}.csv", stations_on(0))]
    if days > CHANGE_DAY_INDEX:
        change_day = start + timedelta(days=CHANGE_DAY_INDEX)
        station_files.append(write_stations(raw_dir / f"stations_{change_day.isoformat()}.csv", stations_on(3)))
    trip_files: list[Path] = []
    previous_first: dict[str, str] | None = None
    for i in range(days):
        day = start + timedelta(days=i)
        as_json = i % 2 == 1
        stations = stations_on(i)
        tag = day.strftime("%Y%m%d")
        rows = [_trip(rng, f"T{tag}-{n:04d}", day, stations, as_json) for n in range(1, trips_per_day + 1)]
        rows.append(dict(rows[0]))
        bad_time = _trip(rng, f"T{tag}-X001", day, stations, as_json)
        bad_time["start_time"] = "yesterday-ish" if as_json else "2026-13-45 99:00:00"
        unknown = _trip(rng, f"T{tag}-X002", day, stations, as_json)
        unknown["end_station_id"] = UNKNOWN_STATION
        backwards = _trip(rng, f"T{tag}-X003", day, stations, as_json)
        backwards["start_time"], backwards["end_time"] = backwards["end_time"], backwards["start_time"]
        rows.extend([bad_time, unknown, backwards])
        if i >= 1:
            prev = day - timedelta(days=1)
            prev_tag = prev.strftime("%Y%m%d")
            rows.extend(
                _trip(rng, f"T{prev_tag}-L{k:03d}", prev, stations_on(i - 1), as_json, early=True) for k in (1, 2)
            )
        if i >= 2 and previous_first is not None:
            rows.append(dict(previous_first))
        previous_first = rows[0]
        rng.shuffle(rows)
        path = raw_dir / f"trips_{day.isoformat()}.{'jsonl' if as_json else 'csv'}"
        _write_trips(path, rows)
        trip_files.append(path)
    return GeneratedFiles(trip_files=trip_files, station_files=station_files)
