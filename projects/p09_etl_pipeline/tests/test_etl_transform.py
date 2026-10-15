"""Milestone 3: normalization to UTC, durations, deduplication, and enrichment."""

from datetime import UTC, date, datetime

from etl.models import Station
from etl.transform import dedupe, enrich, normalize, transform

STATIONS = {"S01": Station("S01", "Union Square", 30), "S02": Station("S02", "City Hall", 24)}


def row(trip_id: str = "T1", start: str = "2026-03-05 08:00:00", end: str = "2026-03-05 08:20:30") -> dict[str, str]:
    return {
        "trip_id": trip_id,
        "start_time": start,
        "end_time": end,
        "start_station_id": "S01",
        "end_station_id": "S02",
        "bike_id": "B1",
        "member_type": "casual",
    }


def test_normalize_utc_and_duration() -> None:
    trip = normalize(row())
    assert trip.start_utc == datetime(2026, 3, 5, 13, 0, tzinfo=UTC), "naive local time converted to UTC"
    assert trip.duration_s == 1230, "20 minutes 30 seconds"


def test_duration_across_dst_switch_uses_real_elapsed_time() -> None:
    trip = normalize(row(start="2026-03-08 01:30:00", end="2026-03-08 03:30:00"))
    assert trip.duration_s == 3600, "clocks jump 02:00 -> 03:00, so only one real hour passes"


def test_local_date_is_business_day_not_utc_day() -> None:
    trip = normalize(row(start="2026-03-05 21:30:00", end="2026-03-05 21:50:00"))
    assert trip.start_utc.date() == date(2026, 3, 6), "21:30 EST is already the next day in UTC"
    assert trip.local_date == date(2026, 3, 5), "local_date is the local calendar day"


def test_mixed_formats_normalize_to_same_instant() -> None:
    a = normalize(row(start="2026-03-05 08:00:00", end="2026-03-05 08:10:00"))
    b = normalize(row(start="2026-03-05T08:00:00-05:00", end="2026-03-05T08:10:00-05:00"))
    assert a == b, "CSV naive and JSON offset forms of the same trip are equal after normalization"


def test_dedupe_keeps_first_and_counts() -> None:
    trips = [normalize(row("A")), normalize(row("B")), normalize(row("A", end="2026-03-05 09:00:00"))]
    unique, removed = dedupe(trips)
    assert [t.trip_id for t in unique] == ["A", "B"] and removed == 1
    assert unique[0].duration_s == 1230, "the first occurrence wins"


def test_enrich_adds_station_names() -> None:
    (trip,) = enrich([normalize(row())], STATIONS)
    assert (trip.start_station_name, trip.end_station_name) == ("Union Square", "City Hall")


def test_enrich_unknown_station_is_blank() -> None:
    (trip,) = enrich([normalize(row())], {})
    assert trip.start_station_name == "", "missing stations enrich to an empty name"


def test_transform_pipeline() -> None:
    trips, removed = transform([row("A"), row("A"), row("B")], STATIONS)
    assert len(trips) == 2 and removed == 1 and trips[0].start_station_name == "Union Square"
