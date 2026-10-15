"""Milestone 6: the end-to-end incremental pipeline, idempotency, late data, and analytics."""

import json
import shutil
from pathlib import Path

import pytest
from etl.analytics import daily_trips, top_routes
from etl.generator import generate
from etl.pipeline import run_pipeline
from etl.warehouse import connect


@pytest.fixture
def source(tmp_path: Path) -> Path:
    generate(tmp_path / "source")
    return tmp_path / "source"


def deliver(source: Path, raw: Path, *names: str) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copy(source / name, raw / name)


def test_full_run_counts(source: Path, tmp_path: Path) -> None:
    s = run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    assert len(s.files_processed) == 9, "2 station snapshots + 7 trip files"
    assert s.rows_read == 255 and s.rows_rejected == 21 and s.rows_valid == 234
    assert s.duplicates_removed == 12, "7 in-file duplicates + 5 re-deliveries"
    assert s.trips_loaded == 222 and s.fact_trip_rows == 222
    assert s.station_versions == 11, "8 stations + 2 changed versions + 1 new station"
    assert s.late_records == 0, "nothing is late on the very first load"


def test_rejected_reasons_in_summary_and_report(source: Path, tmp_path: Path) -> None:
    s = run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    assert s.rejected_by_reason == {
        "bad_timestamp:start_time": 7,
        "end_before_start": 7,
        "unknown_station:end_station_id": 7,
    }
    lines = (tmp_path / "state" / "rejected.jsonl").read_text().splitlines()
    assert len(lines) == 21, "every rejected row is written to the report"
    assert all(json.loads(line)["reasons"] for line in lines), "each report line explains why"


def test_second_run_is_a_noop(source: Path, tmp_path: Path) -> None:
    run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    s = run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    assert s.files_processed == [] and s.trips_loaded == 0, "the manifest makes re-runs skip processed files"
    assert s.fact_trip_rows == 222 and s.station_versions == 11


def test_reprocessing_everything_is_idempotent(source: Path, tmp_path: Path) -> None:
    db = tmp_path / "wh.db"
    first = run_pipeline(source, db, tmp_path / "state")
    (tmp_path / "state" / "manifest.json").unlink()
    second = run_pipeline(source, db, tmp_path / "state")
    assert second.files_processed == first.files_processed, "without a manifest every file is read again"
    assert (second.fact_trip_rows, second.station_versions) == (222, 11), "upserts + SCD2 no-ops: same row counts"


def test_incremental_daily_runs_match_full_run(source: Path, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    names = sorted(p.name for p in source.iterdir())
    stations = [n for n in names if n.startswith("stations_")]
    trips = [n for n in names if n.startswith("trips_")]
    summaries = []
    for i, trip_file in enumerate(trips):
        deliver(source, raw, trip_file, *(s for s in stations if s.split("_")[1][:10] <= trip_file.split("_")[1][:10]))
        summaries.append(run_pipeline(raw, tmp_path / "wh.db", tmp_path / "state"))
        assert summaries[-1].files_processed[-1] == trip_file, f"run {i} processes only the new day"
    assert summaries[-1].fact_trip_rows == 222, "daily incremental loads end with the same facts as one full load"
    assert summaries[-1].station_versions == 11


def test_late_records_are_loaded_and_counted(source: Path, tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    deliver(source, raw, "stations_2026-03-05.csv", "trips_2026-03-05.csv")
    first = run_pipeline(raw, tmp_path / "wh.db", tmp_path / "state")
    deliver(source, raw, "trips_2026-03-06.jsonl")
    second = run_pipeline(raw, tmp_path / "wh.db", tmp_path / "state")
    assert second.late_records == 2, "two trips from 2026-03-05 arrive in the 2026-03-06 file"
    conn = connect(tmp_path / "wh.db")
    late = conn.execute("SELECT date_key FROM fact_trip WHERE trip_id LIKE '%-L%'").fetchall()
    conn.close()
    assert late == [(20260305,), (20260305,)], "late trips land on their real business day"
    assert second.watermark is not None and first.watermark is not None and second.watermark > first.watermark


def test_scd2_history_from_pipeline(source: Path, tmp_path: Path) -> None:
    run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    conn = connect(tmp_path / "wh.db")
    names = conn.execute(
        "SELECT DISTINCT s.name FROM fact_trip f JOIN dim_station s ON s.station_key IN "
        "(f.start_station_key, f.end_station_key) WHERE s.station_id = 'S03' ORDER BY s.name"
    ).fetchall()
    conn.close()
    assert names == [("Harbor Point",), ("Harbor Point Plaza",)], (
        "trips before the rename point at the old version, trips after at the new one"
    )


def test_daily_trips_moving_average(source: Path, tmp_path: Path) -> None:
    run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    conn = connect(tmp_path / "wh.db")
    rows = daily_trips(conn, window=7)
    three = daily_trips(conn, window=3)
    conn.close()
    assert [r.day for r in rows][:2] == ["2026-03-05", "2026-03-06"] and len(rows) == 7
    assert sum(r.trips for r in rows) == 222
    assert rows[-1].moving_avg == round(222 / 7, 2), "the 7th day averages all seven days"
    assert three[-1].moving_avg == round((32 + 32 + 30) / 3, 2), "a 3-day window averages the last three"


def test_daily_trips_rejects_bad_window(tmp_path: Path) -> None:
    conn = connect(":memory:")
    with pytest.raises(ValueError):
        daily_trips(conn, window=0)
    conn.close()


def test_top_routes(source: Path, tmp_path: Path) -> None:
    run_pipeline(source, tmp_path / "wh.db", tmp_path / "state")
    conn = connect(tmp_path / "wh.db")
    routes = top_routes(conn, limit=3)
    conn.close()
    assert len(routes) == 3 and routes[0].rank == 1
    assert routes[0].trips >= routes[1].trips >= routes[2].trips, "ordered by trips descending"
    assert (routes[0].start_name, routes[0].end_name, routes[0].trips) == ("Union Square", "Riverside Park", 7)
    assert routes[1].rank == routes[2].rank == 2, "RANK() gives ties the same rank"
