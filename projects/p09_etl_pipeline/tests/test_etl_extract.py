"""Milestone 1: generator determinism, manifest, and file readers."""

import json
from pathlib import Path

from etl.extract import Manifest, discover_new_files, read_station_file, read_trip_file, snapshot_date
from etl.generator import generate


def test_generator_is_deterministic(tmp_path: Path) -> None:
    a = generate(tmp_path / "a")
    b = generate(tmp_path / "b")
    for pa, pb in zip(a.trip_files + a.station_files, b.trip_files + b.station_files, strict=True):
        assert pa.read_bytes() == pb.read_bytes(), f"{pa.name} differs between two runs with the same seed"


def test_generator_alternates_csv_and_jsonl(tmp_path: Path) -> None:
    files = generate(tmp_path).trip_files
    assert [p.suffix for p in files[:3]] == [".csv", ".jsonl", ".csv"], "days alternate CSV and JSON Lines"


def test_manifest_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state" / "manifest.json"
    m = Manifest.load(path)
    assert not m.is_processed("trips_2026-03-05.csv"), "a new manifest is empty"
    m.mark("trips_2026-03-05.csv")
    m.save()
    again = Manifest.load(path)
    assert again.is_processed("trips_2026-03-05.csv"), "marks survive save/load"
    assert json.loads(path.read_text())["processed"] == ["trips_2026-03-05.csv"], "manifest stores a sorted list"


def test_manifest_mark_is_not_persisted_until_save(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    m = Manifest.load(path)
    m.mark("x.csv")
    assert not path.exists(), "mark() must not write the file; only save() does"


def test_discover_skips_processed_files_and_sorts(tmp_path: Path) -> None:
    generate(tmp_path)
    m = Manifest(tmp_path / "manifest.json", {"trips_2026-03-05.csv"})
    names = [p.name for p in discover_new_files(tmp_path, m, "trips_*")]
    assert names[0] == "trips_2026-03-06.jsonl", "processed files are skipped and the rest sorted by name/date"
    assert len(names) == 6, "seven files minus one processed"


def test_read_csv_rows_are_strings_with_source(tmp_path: Path) -> None:
    path = generate(tmp_path).trip_files[0]
    rows = read_trip_file(path)
    assert all(isinstance(v, str) for row in rows for v in row.values()), "every value is a string"
    assert rows[0]["_source"] == path.name, "each row records its source file in _source"
    assert len(rows) == 34, "day 1: 30 trips + 1 duplicate + 3 bad rows"


def test_read_jsonl_and_malformed_line(tmp_path: Path) -> None:
    path = tmp_path / "trips_2026-01-01.jsonl"
    path.write_text('{"trip_id": "T1", "bike_id": 7, "member_type": null}\n\nnot json\n', encoding="utf-8")
    rows = read_trip_file(path)
    assert rows[0]["bike_id"] == "7" and rows[0]["member_type"] == "", "JSON values become strings; null becomes ''"
    assert len(rows) == 2, "blank lines are skipped"
    assert rows[1]["_error"].startswith("bad_json"), "a malformed line becomes an _error row instead of crashing"


def test_read_unsupported_extension_raises(tmp_path: Path) -> None:
    path = tmp_path / "trips.xml"
    path.write_text("<x/>")
    try:
        read_trip_file(path)
    except ValueError:
        return
    raise AssertionError("an unknown extension should raise ValueError")


def test_read_station_file_and_snapshot_date(tmp_path: Path) -> None:
    files = generate(tmp_path).station_files
    stations = read_station_file(files[1])
    assert snapshot_date(files[1]) == "2026-03-08", "the snapshot date comes from the file name"
    by_id = {s.station_id: s for s in stations}
    assert by_id["S03"].name == "Harbor Point Plaza", "the second snapshot renames S03"
    assert by_id["S07"].capacity == 32, "capacity is parsed as an int"
