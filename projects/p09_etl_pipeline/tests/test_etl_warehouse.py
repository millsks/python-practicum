"""Milestone 4: star schema, SCD type 2 stations, idempotent upserts, and the watermark."""

import sqlite3
from datetime import UTC, date, datetime, timedelta

import pytest
from etl.models import Station, Trip
from etl.warehouse import (
    apply_station_snapshot,
    connect,
    current_stations,
    date_key,
    ensure_dates,
    get_watermark,
    load_trips,
    set_watermark,
    station_key_at,
    table_count,
)

V1 = [Station("S01", "Union Square", 30), Station("S03", "Harbor Point", 20)]
V2 = [Station("S01", "Union Square", 30), Station("S03", "Harbor Point Plaza", 20)]


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = connect(":memory:")
    yield c
    c.close()


def make_trip(trip_id: str, day: date, minutes: int = 10) -> Trip:
    start = datetime(day.year, day.month, day.day, 14, tzinfo=UTC)
    return Trip(trip_id, start, start + timedelta(minutes=minutes), minutes * 60, "S01", "S03", "B1", "member", day)


def test_schema_tables_exist(conn: sqlite3.Connection) -> None:
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"dim_station", "dim_date", "fact_trip", "etl_state"} <= names, "connect() creates the star schema"


def test_connect_is_idempotent(tmp_path) -> None:
    connect(tmp_path / "w.db").close()
    connect(tmp_path / "w.db").close()  # must not fail on existing tables


def test_date_key_and_dim_date(conn: sqlite3.Connection) -> None:
    assert date_key(date(2026, 3, 7)) == 20260307
    assert ensure_dates(conn, [date(2026, 3, 7), date(2026, 3, 7), date(2026, 3, 9)]) == 2
    assert ensure_dates(conn, [date(2026, 3, 7)]) == 0, "existing dates are not inserted again"
    row = conn.execute("SELECT weekday, is_weekend FROM dim_date WHERE date_key = 20260307").fetchone()
    assert row == ("Saturday", 1), "2026-03-07 is a Saturday"


def test_scd2_first_snapshot_inserts(conn: sqlite3.Connection) -> None:
    changes = apply_station_snapshot(conn, V1, date(2026, 3, 5))
    assert (changes.inserted, changes.updated, changes.unchanged) == (2, 0, 0)
    assert table_count(conn, "dim_station") == 2


def test_scd2_rename_closes_old_version(conn: sqlite3.Connection) -> None:
    apply_station_snapshot(conn, V1, date(2026, 3, 5))
    changes = apply_station_snapshot(conn, V2, date(2026, 3, 8))
    assert (changes.inserted, changes.updated, changes.unchanged) == (0, 1, 1)
    history = conn.execute(
        "SELECT name, valid_from, valid_to, is_current FROM dim_station WHERE station_id = 'S03' ORDER BY valid_from"
    ).fetchall()
    assert history == [
        ("Harbor Point", "2026-03-05", "2026-03-08", 0),
        ("Harbor Point Plaza", "2026-03-08", None, 1),
    ], "SCD2 keeps the old row (closed) and adds a new current row"


def test_scd2_reapply_is_noop(conn: sqlite3.Connection) -> None:
    apply_station_snapshot(conn, V1, date(2026, 3, 5))
    apply_station_snapshot(conn, V2, date(2026, 3, 8))
    apply_station_snapshot(conn, V2, date(2026, 3, 8))
    apply_station_snapshot(conn, V1, date(2026, 3, 5))
    assert table_count(conn, "dim_station") == 3, "re-applying any snapshot adds no versions"
    assert current_stations(conn)["S03"].name == "Harbor Point Plaza", "an older snapshot never overwrites newer"


def test_point_in_time_station_lookup(conn: sqlite3.Connection) -> None:
    apply_station_snapshot(conn, V1, date(2026, 3, 5))
    apply_station_snapshot(conn, V2, date(2026, 3, 8))
    old = station_key_at(conn, "S03", date(2026, 3, 7))
    new = station_key_at(conn, "S03", date(2026, 3, 8))
    names = dict(conn.execute("SELECT station_key, name FROM dim_station"))
    assert names[old] == "Harbor Point" and names[new] == "Harbor Point Plaza", "facts join the version in effect"
    assert station_key_at(conn, "S03", date(2026, 1, 1)) == old, "before the first version, use the earliest"
    assert station_key_at(conn, "S77", date(2026, 3, 7)) is None


def test_load_trips_is_idempotent(conn: sqlite3.Connection) -> None:
    apply_station_snapshot(conn, V1, date(2026, 3, 5))
    trips = [make_trip("T1", date(2026, 3, 5)), make_trip("T2", date(2026, 3, 6))]
    assert load_trips(conn, trips) == 2
    load_trips(conn, trips)
    assert table_count(conn, "fact_trip") == 2, "loading the same trips twice must not duplicate rows"
    assert table_count(conn, "dim_date") == 2


def test_upsert_updates_existing_row(conn: sqlite3.Connection) -> None:
    apply_station_snapshot(conn, V1, date(2026, 3, 5))
    load_trips(conn, [make_trip("T1", date(2026, 3, 5), minutes=10)])
    load_trips(conn, [make_trip("T1", date(2026, 3, 5), minutes=25)])
    assert conn.execute("SELECT duration_s FROM fact_trip WHERE trip_id = 'T1'").fetchone() == (1500,), (
        "ON CONFLICT DO UPDATE keeps the latest values"
    )


def test_load_unknown_station_raises_and_rolls_back(conn: sqlite3.Connection) -> None:
    good = make_trip("T1", date(2026, 3, 5))
    with pytest.raises(KeyError):
        load_trips(conn, [good])  # no stations loaded yet
    assert table_count(conn, "fact_trip") == 0, "a failed load leaves no partial rows"


def test_watermark_only_moves_forward(conn: sqlite3.Connection) -> None:
    assert get_watermark(conn) is None, "no watermark before the first load"
    assert set_watermark(conn, "2026-03-06T10:00:00+00:00") == "2026-03-06T10:00:00+00:00"
    assert set_watermark(conn, "2026-03-05T10:00:00+00:00") == "2026-03-06T10:00:00+00:00", "never moves back"
    assert get_watermark(conn) == "2026-03-06T10:00:00+00:00"


def test_table_count_rejects_unknown_table(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        table_count(conn, "users; DROP TABLE fact_trip")
