"""Transform: normalize valid rows into :class:`~etl.models.Trip` objects, dedupe, and enrich."""

from collections.abc import Iterable, Mapping
from datetime import tzinfo

from etl.models import LOCAL_TZ, RawRow, Station, Trip


def normalize(row: RawRow, local_tz: tzinfo = LOCAL_TZ) -> Trip:
    """Convert one validated raw row to a :class:`Trip` with UTC times and a duration.

    Args:
        row: A row that passed validation.
        local_tz: Zone for naive timestamps and for the business date.

    Returns:
        The normalized trip (not yet enriched with station names).
    """
    # TODO: parse both timestamps to UTC, duration in whole seconds, local_date in local_tz
    raise NotImplementedError


def dedupe(trips: Iterable[Trip]) -> tuple[list[Trip], int]:
    """Drop repeated ``trip_id`` values, keeping the first occurrence.

    Args:
        trips: Trips in arrival order.

    Returns:
        The unique trips (order preserved) and how many duplicates were dropped.
    """
    # TODO: keep the first trip per trip_id; count the rest
    raise NotImplementedError


def enrich(trips: Iterable[Trip], stations: Mapping[str, Station]) -> list[Trip]:
    """Attach station names from the station dimension.

    Args:
        trips: Normalized trips.
        stations: Current stations keyed by ``station_id``.

    Returns:
        New trips with ``start_station_name`` and ``end_station_name`` filled in (``""`` if unknown).
    """
    # TODO: dataclasses.replace(trip, start_station_name=..., end_station_name=...)
    raise NotImplementedError


def transform(rows: Iterable[RawRow], stations: Mapping[str, Station]) -> tuple[list[Trip], int]:
    """Normalize, dedupe, and enrich validated rows.

    Args:
        rows: Rows that passed validation, in arrival order.
        stations: Current stations keyed by ``station_id``.

    Returns:
        The trips to load and the number of duplicates removed.
    """
    # TODO: normalize every row, dedupe, then enrich
    raise NotImplementedError
