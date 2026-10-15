"""Milestone 2: the validation rule engine and rejection reasons."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from etl.models import Rejection
from etl.validate import (
    Rule,
    default_rules,
    parse_timestamp,
    reason_counts,
    validate,
    write_rejection_report,
)

KNOWN = {"S01", "S02"}


def good_row(**changes: str) -> dict[str, str]:
    row = {
        "trip_id": "T1",
        "start_time": "2026-03-05 08:00:00",
        "end_time": "2026-03-05 08:20:00",
        "start_station_id": "S01",
        "end_station_id": "S02",
        "bike_id": "B1",
        "member_type": "member",
    }
    return row | changes


def reasons_for(row: dict[str, str]) -> tuple[str, ...]:
    result = validate([row], default_rules(KNOWN))
    return result.rejected[0].reasons if result.rejected else ()


def test_parse_naive_timestamp_is_local_then_utc() -> None:
    assert parse_timestamp("2026-03-05 08:00:00") == datetime(2026, 3, 5, 13, 0, tzinfo=UTC), "EST is UTC-5"


def test_parse_naive_timestamp_after_dst_switch() -> None:
    assert parse_timestamp("2026-03-09 08:00:00") == datetime(2026, 3, 9, 12, 0, tzinfo=UTC), "EDT is UTC-4"


def test_parse_offset_timestamp_keeps_offset() -> None:
    assert parse_timestamp("2026-03-05T08:00:00-05:00").utcoffset() is not None, "result is timezone-aware"
    assert parse_timestamp("2026-03-05T13:00:00+00:00") == datetime(2026, 3, 5, 13, tzinfo=UTC)


def test_parse_bad_timestamp_raises() -> None:
    with pytest.raises(ValueError):
        parse_timestamp("2026-13-45 99:00:00")


def test_good_row_passes() -> None:
    assert reasons_for(good_row()) == (), "a clean row has no reasons"


def test_missing_field_reason() -> None:
    assert "missing:bike_id" in reasons_for(good_row(bike_id="")), "empty required field -> missing:<field>"


def test_bad_timestamp_reason() -> None:
    assert reasons_for(good_row(start_time="yesterday")) == ("bad_timestamp:start_time",)


def test_end_before_start_reason() -> None:
    assert reasons_for(good_row(end_time="2026-03-05 07:00:00")) == ("end_before_start",)


def test_duration_too_long_reason() -> None:
    assert reasons_for(good_row(end_time="2026-03-07 08:00:00")) == ("duration_too_long",)


def test_unknown_station_reason() -> None:
    assert reasons_for(good_row(end_station_id="S99")) == ("unknown_station:end_station_id",)


def test_bad_member_type_reason() -> None:
    assert reasons_for(good_row(member_type="vip")) == ("bad_member_type",)


def test_all_reasons_collected() -> None:
    reasons = reasons_for(good_row(start_station_id="S98", member_type="vip", end_time="nope"))
    assert set(reasons) == {"unknown_station:start_station_id", "bad_member_type", "bad_timestamp:end_time"}, (
        "validation runs every rule and reports every problem, not just the first"
    )


def test_json_error_row_is_rejected() -> None:
    assert reasons_for({"_error": "bad_json:line3", "_source": "x.jsonl"}) == ("bad_json:line3",)


def test_custom_rule_and_order_preserved() -> None:
    no_b2 = Rule("no_b2", lambda row: ["banned_bike"] if row.get("bike_id") == "B2" else [])
    rows = [good_row(trip_id="A"), good_row(trip_id="B", bike_id="B2"), good_row(trip_id="C")]
    result = validate(rows, [*default_rules(KNOWN), no_b2])
    assert [r["trip_id"] for r in result.valid] == ["A", "C"], "valid rows keep input order"
    assert result.rejected[0].row["trip_id"] == "B" and result.rejected[0].reasons == ("banned_bike",)


def test_reason_counts() -> None:
    rej = [Rejection({}, ("a", "b")), Rejection({}, ("a",))]
    assert reason_counts(rej) == {"a": 2, "b": 1}


def test_write_rejection_report_appends_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "out" / "rejected.jsonl"
    assert write_rejection_report([Rejection({"trip_id": "T9"}, ("x",))], path) == 1
    write_rejection_report([Rejection({"trip_id": "T10"}, ("y",))], path)
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert [line["row"]["trip_id"] for line in lines] == ["T9", "T10"], "the report is appended, one JSON per line"
    assert lines[0]["reasons"] == ["x"], "each line carries its reasons"
