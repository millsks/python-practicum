"""Load: a sqlite3 star schema with an SCD type 2 station dimension, idempotent upserts, and a watermark."""

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from etl.models import Station, Trip

SCHEMA = """
CREATE TABLE IF NOT EXISTS dim_station (
    station_key INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id  TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    capacity    INTEGER NOT NULL,
    valid_from  TEXT    NOT NULL,
    valid_to    TEXT,
    is_current  INTEGER NOT NULL CHECK (is_current IN (0, 1)),
    UNIQUE (station_id, valid_from)
);
CREATE INDEX IF NOT EXISTS ix_dim_station_current ON dim_station (station_id, is_current);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key   INTEGER PRIMARY KEY,
    date       TEXT    NOT NULL UNIQUE,
    year       INTEGER NOT NULL,
    month      INTEGER NOT NULL,
    day        INTEGER NOT NULL,
    weekday    TEXT    NOT NULL,
    is_weekend INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_trip (
    trip_id           TEXT    PRIMARY KEY,
    date_key          INTEGER NOT NULL REFERENCES dim_date (date_key),
    start_station_key INTEGER NOT NULL REFERENCES dim_station (station_key),
    end_station_key   INTEGER NOT NULL REFERENCES dim_station (station_key),
    start_utc         TEXT    NOT NULL,
    end_utc           TEXT    NOT NULL,
    duration_s        INTEGER NOT NULL,
    bike_id           TEXT    NOT NULL,
    member_type       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_fact_trip_date ON fact_trip (date_key);

CREATE TABLE IF NOT EXISTS etl_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

WATERMARK_KEY = "trip_watermark"


@dataclass(frozen=True, slots=True)
class StationChanges:
    """What applying a station snapshot did.

    Attributes:
        inserted: Stations seen for the first time.
        updated: Stations whose attributes changed (old version closed, new version opened).
        unchanged: Stations identical to their current version.
    """

    inserted: int
    updated: int
    unchanged: int


def connect(path: Path | str) -> sqlite3.Connection:
    """Open the warehouse and make sure the schema exists.

    Args:
        path: Database file, or ``":memory:"``.

    Returns:
        A connection with foreign keys enabled and the schema created.
    """
    # TODO: sqlite3.connect, PRAGMA foreign_keys = ON, executescript(SCHEMA)
    raise NotImplementedError


def date_key(day: date) -> int:
    """Return the ``YYYYMMDD`` integer surrogate key for a date.

    Args:
        day: Calendar date.

    Returns:
        For example ``20260305``.
    """
    # TODO: YYYYMMDD as an int
    raise NotImplementedError


def ensure_dates(conn: sqlite3.Connection, days: Iterable[date]) -> int:
    """Insert any missing ``dim_date`` rows.

    Args:
        conn: Warehouse connection.
        days: Dates referenced by facts.

    Returns:
        Number of new rows.
    """
    # TODO: INSERT OR IGNORE one dim_date row per distinct date; return conn.total_changes delta
    raise NotImplementedError


def apply_station_snapshot(conn: sqlite3.Connection, stations: Iterable[Station], as_of: date) -> StationChanges:
    """Merge a station snapshot into ``dim_station`` as slowly changing dimension type 2.

    A new station gets a current row valid from ``as_of``. A changed station has its current row closed
    (``valid_to = as_of``, ``is_current = 0``) and a new current row opened. Identical stations are left alone,
    and snapshots older than a station's current version are ignored, so re-applying any snapshot is a no-op.

    Args:
        conn: Warehouse connection.
        stations: Stations in the snapshot.
        as_of: Date the snapshot takes effect.

    Returns:
        Counts of inserted, updated, and unchanged stations.
    """
    # TODO: SCD2: insert new; close + insert changed (valid_to = as_of, is_current = 0); ignore identical or older
    raise NotImplementedError


def current_stations(conn: sqlite3.Connection) -> dict[str, Station]:
    """Return the current version of every station.

    Args:
        conn: Warehouse connection.

    Returns:
        Stations keyed by ``station_id``.
    """
    # TODO: SELECT ... WHERE is_current = 1
    raise NotImplementedError


def station_key_at(conn: sqlite3.Connection, station_id: str, day: date) -> int | None:
    """Find the ``dim_station`` version in effect on ``day`` (a point-in-time lookup).

    If ``day`` is before the first version, the earliest version is used.

    Args:
        conn: Warehouse connection.
        station_id: Natural key.
        day: Business date of the fact.

    Returns:
        The surrogate ``station_key``, or ``None`` if the station is unknown.
    """
    # TODO: valid_from <= day AND (valid_to IS NULL OR day < valid_to); fall back to the earliest version
    raise NotImplementedError


def load_trips(conn: sqlite3.Connection, trips: Iterable[Trip]) -> int:
    """Upsert trips into ``fact_trip`` in one transaction.

    ``INSERT ... ON CONFLICT (trip_id) DO UPDATE`` makes the load idempotent: loading the same trip twice leaves one
    row holding the latest values.

    Args:
        conn: Warehouse connection.
        trips: Trips to load.

    Returns:
        Number of trips upserted.

    Raises:
        KeyError: If a trip references a station missing from ``dim_station``.
    """
    # TODO: one transaction: ensure_dates, look up station keys, INSERT ... ON CONFLICT (trip_id) DO UPDATE
    raise NotImplementedError


def get_watermark(conn: sqlite3.Connection) -> str | None:
    """Return the stored watermark (latest loaded ``start_utc``), or ``None`` before the first load.

    Args:
        conn: Warehouse connection.

    Returns:
        An ISO-8601 UTC timestamp string, or ``None``.
    """
    # TODO: read etl_state[WATERMARK_KEY]
    raise NotImplementedError


def set_watermark(conn: sqlite3.Connection, value: str) -> str:
    """Advance the watermark; it never moves backwards.

    Args:
        conn: Warehouse connection.
        value: Candidate ISO-8601 UTC timestamp.

    Returns:
        The stored watermark after the update.
    """
    # TODO: upsert max(current, value) into etl_state
    raise NotImplementedError


def table_count(conn: sqlite3.Connection, table: str) -> int:
    """Return the number of rows in one of the warehouse tables.

    Args:
        conn: Warehouse connection.
        table: One of ``dim_station``, ``dim_date``, ``fact_trip``, ``etl_state``.

    Returns:
        The row count.

    Raises:
        ValueError: For any other table name (guards the f-string against SQL injection).
    """
    # TODO: whitelist the table name before using it in an f-string
    raise NotImplementedError
