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
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def date_key(day: date) -> int:
    """Return the ``YYYYMMDD`` integer surrogate key for a date.

    Args:
        day: Calendar date.

    Returns:
        For example ``20260305``.
    """
    return day.year * 10_000 + day.month * 100 + day.day


def ensure_dates(conn: sqlite3.Connection, days: Iterable[date]) -> int:
    """Insert any missing ``dim_date`` rows.

    Args:
        conn: Warehouse connection.
        days: Dates referenced by facts.

    Returns:
        Number of new rows.
    """
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO dim_date (date_key, date, year, month, day, weekday, is_weekend) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (date_key(d), d.isoformat(), d.year, d.month, d.day, d.strftime("%A"), int(d.weekday() >= 5))
            for d in sorted(set(days))
        ],
    )
    return conn.total_changes - before


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
    inserted = updated = unchanged = 0
    day = as_of.isoformat()
    with conn:
        for s in stations:
            current = conn.execute(
                "SELECT station_key, name, capacity, valid_from FROM dim_station WHERE station_id = ? AND is_current = 1",
                (s.station_id,),
            ).fetchone()
            if current is None:
                conn.execute(
                    "INSERT INTO dim_station (station_id, name, capacity, valid_from, valid_to, is_current) "
                    "VALUES (?, ?, ?, ?, NULL, 1)",
                    (s.station_id, s.name, s.capacity, day),
                )
                inserted += 1
            elif (current[1], current[2]) == (s.name, s.capacity) or day <= current[3]:
                unchanged += 1
            else:
                conn.execute(
                    "UPDATE dim_station SET valid_to = ?, is_current = 0 WHERE station_key = ?", (day, current[0])
                )
                conn.execute(
                    "INSERT INTO dim_station (station_id, name, capacity, valid_from, valid_to, is_current) "
                    "VALUES (?, ?, ?, ?, NULL, 1)",
                    (s.station_id, s.name, s.capacity, day),
                )
                updated += 1
    return StationChanges(inserted, updated, unchanged)


def current_stations(conn: sqlite3.Connection) -> dict[str, Station]:
    """Return the current version of every station.

    Args:
        conn: Warehouse connection.

    Returns:
        Stations keyed by ``station_id``.
    """
    rows = conn.execute("SELECT station_id, name, capacity FROM dim_station WHERE is_current = 1")
    return {r[0]: Station(r[0], r[1], r[2]) for r in rows}


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
    iso = day.isoformat()
    row = conn.execute(
        "SELECT station_key FROM dim_station WHERE station_id = ? AND valid_from <= ? "
        "AND (valid_to IS NULL OR ? < valid_to) ORDER BY valid_from DESC LIMIT 1",
        (station_id, iso, iso),
    ).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT station_key FROM dim_station WHERE station_id = ? ORDER BY valid_from LIMIT 1", (station_id,)
        ).fetchone()
    return None if row is None else int(row[0])


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
    batch = list(trips)
    with conn:
        ensure_dates(conn, (t.local_date for t in batch))
        rows = []
        for t in batch:
            start_key = station_key_at(conn, t.start_station_id, t.local_date)
            end_key = station_key_at(conn, t.end_station_id, t.local_date)
            if start_key is None or end_key is None:
                raise KeyError(f"trip {t.trip_id} references an unknown station")
            rows.append(
                (
                    t.trip_id,
                    date_key(t.local_date),
                    start_key,
                    end_key,
                    t.start_utc.isoformat(),
                    t.end_utc.isoformat(),
                    t.duration_s,
                    t.bike_id,
                    t.member_type,
                )
            )
        conn.executemany(
            """
            INSERT INTO fact_trip (trip_id, date_key, start_station_key, end_station_key, start_utc, end_utc,
                                   duration_s, bike_id, member_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (trip_id) DO UPDATE SET
                date_key = excluded.date_key,
                start_station_key = excluded.start_station_key,
                end_station_key = excluded.end_station_key,
                start_utc = excluded.start_utc,
                end_utc = excluded.end_utc,
                duration_s = excluded.duration_s,
                bike_id = excluded.bike_id,
                member_type = excluded.member_type
            """,
            rows,
        )
    return len(rows)


def get_watermark(conn: sqlite3.Connection) -> str | None:
    """Return the stored watermark (latest loaded ``start_utc``), or ``None`` before the first load.

    Args:
        conn: Warehouse connection.

    Returns:
        An ISO-8601 UTC timestamp string, or ``None``.
    """
    row = conn.execute("SELECT value FROM etl_state WHERE key = ?", (WATERMARK_KEY,)).fetchone()
    return None if row is None else str(row[0])


def set_watermark(conn: sqlite3.Connection, value: str) -> str:
    """Advance the watermark; it never moves backwards.

    Args:
        conn: Warehouse connection.
        value: Candidate ISO-8601 UTC timestamp.

    Returns:
        The stored watermark after the update.
    """
    current = get_watermark(conn)
    new = value if current is None or value > current else current
    with conn:
        conn.execute(
            "INSERT INTO etl_state (key, value) VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (WATERMARK_KEY, new),
        )
    return new


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
    if table not in {"dim_station", "dim_date", "fact_trip", "etl_state"}:
        raise ValueError(f"unknown table {table!r}")
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
