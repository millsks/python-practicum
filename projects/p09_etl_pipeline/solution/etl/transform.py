"""Transform: normalize valid rows into :class:`~etl.models.Trip` objects, dedupe, and enrich."""

from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import tzinfo

from etl.models import LOCAL_TZ, RawRow, Station, Trip
from etl.validate import parse_timestamp


def normalize(row: RawRow, local_tz: tzinfo = LOCAL_TZ) -> Trip:
    """Convert one validated raw row to a :class:`Trip` with UTC times and a duration.

    Args:
        row: A row that passed validation.
        local_tz: Zone for naive timestamps and for the business date.

    Returns:
        The normalized trip (not yet enriched with station names).
    """
    start = parse_timestamp(row["start_time"], local_tz)
    end = parse_timestamp(row["end_time"], local_tz)
    return Trip(
        trip_id=row["trip_id"].strip(),
        start_utc=start,
        end_utc=end,
        duration_s=int((end - start).total_seconds()),
        start_station_id=row["start_station_id"].strip(),
        end_station_id=row["end_station_id"].strip(),
        bike_id=row["bike_id"].strip(),
        member_type=row["member_type"].strip(),
        local_date=start.astimezone(local_tz).date(),
    )


def dedupe(trips: Iterable[Trip]) -> tuple[list[Trip], int]:
    """Drop repeated ``trip_id`` values, keeping the first occurrence.

    Args:
        trips: Trips in arrival order.

    Returns:
        The unique trips (order preserved) and how many duplicates were dropped.
    """
    seen: set[str] = set()
    unique: list[Trip] = []
    removed = 0
    for trip in trips:
        if trip.trip_id in seen:
            removed += 1
            continue
        seen.add(trip.trip_id)
        unique.append(trip)
    return unique, removed


def enrich(trips: Iterable[Trip], stations: Mapping[str, Station]) -> list[Trip]:
    """Attach station names from the station dimension.

    Args:
        trips: Normalized trips.
        stations: Current stations keyed by ``station_id``.

    Returns:
        New trips with ``start_station_name`` and ``end_station_name`` filled in (``""`` if unknown).
    """
    out: list[Trip] = []
    for trip in trips:
        start = stations.get(trip.start_station_id)
        end = stations.get(trip.end_station_id)
        out.append(
            replace(
                trip,
                start_station_name=start.name if start else "",
                end_station_name=end.name if end else "",
            )
        )
    return out


def transform(rows: Iterable[RawRow], stations: Mapping[str, Station]) -> tuple[list[Trip], int]:
    """Normalize, dedupe, and enrich validated rows.

    Args:
        rows: Rows that passed validation, in arrival order.
        stations: Current stations keyed by ``station_id``.

    Returns:
        The trips to load and the number of duplicates removed.
    """
    unique, removed = dedupe(normalize(row) for row in rows)
    return enrich(unique, stations), removed
