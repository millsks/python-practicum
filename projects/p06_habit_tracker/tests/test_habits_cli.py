"""Milestone 4: the argparse CLI, run against real SQLite files in ``tmp_path``."""

import csv
import json
from pathlib import Path

import pytest
from habits.cli import main

TODAY = "2026-01-05"


def run(db: Path, *args: str, today: str = TODAY) -> int:
    return main(["--db", str(db), "--today", today, *args])


@pytest.fixture
def db(tmp_path: Path) -> Path:
    return tmp_path / "habits.db"


def test_add_and_list(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(db, "add", "Drink Water", "--frequency", "mon,wed") == 0
    assert run(db, "list") == 0
    out = capsys.readouterr().out
    assert "created drink-water (mon,wed)" in out
    assert "drink-water\tDrink Water\tmon,wed" in out


def test_list_when_empty(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(db, "list") == 0
    assert "no habits yet" in capsys.readouterr().out


def test_checkin_twice(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(db, "add", "Read")
    assert run(db, "checkin", "read") == 0
    assert run(db, "checkin", "read") == 0
    out = capsys.readouterr().out
    assert "checked in read" in out
    assert "read already done this period" in out


def test_stats(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(db, "add", "Read")
    run(db, "checkin", "read")
    run(db, "checkin", "read", today="2026-01-06")
    assert run(db, "stats", "read", today="2026-01-06") == 0
    out = capsys.readouterr().out
    assert "current_streak: 2" in out and "completed: 2/2" in out and "completion_rate: 100.0%" in out


def test_checkin_backfill_with_date(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(db, "add", "Read")
    assert run(db, "checkin", "read", "--date", "2026-01-06", today="2026-01-08") == 0
    assert run(db, "stats", "read", "--from", "2026-01-05", "--to", "2026-01-06", today="2026-01-08") == 0
    assert "completed: 1/2" in capsys.readouterr().out


def test_undo_and_archive(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(db, "add", "Read")
    run(db, "add", "Walk")
    run(db, "checkin", "read")
    assert run(db, "undo", "read") == 0
    assert run(db, "undo", "read") == 0
    assert run(db, "archive", "walk") == 0
    run(db, "list")
    out = capsys.readouterr().out
    assert "undid read" in out and "nothing to undo for read" in out and "archived walk" in out
    assert "walk\tWalk" not in out.split("archived walk")[-1], "archived habits are hidden from list"
    run(db, "list", "--all")
    assert "walk\tWalk\tdaily\tarchived" in capsys.readouterr().out


def test_export_json_to_stdout(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(db, "add", "Read")
    run(db, "checkin", "read")
    capsys.readouterr()
    assert run(db, "export", "--format", "json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["completions"] == [TODAY], "stdout must contain only the JSON document"


def test_export_csv_to_file(db: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run(db, "add", "Read")
    target = tmp_path / "out.csv"
    assert run(db, "export", "--format", "csv", "--output", str(target)) == 0
    assert "exported to" in capsys.readouterr().out
    rows = list(csv.DictReader(target.open(encoding="utf-8")))
    assert rows[0]["id"] == "read"


def test_habit_error_returns_1(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(db, "checkin", "ghost") == 1
    captured = capsys.readouterr()
    assert "error: no habit 'ghost'" in captured.err
    assert captured.out == "", "errors must not pollute stdout"


def test_bad_date_is_usage_error(db: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        run(db, "checkin", "read", "--date", "yesterday")
    assert excinfo.value.code == 2


def test_db_from_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "env.db"
    monkeypatch.setenv("HABITS_DB", str(target))
    assert main(["--today", TODAY, "add", "Read"]) == 0
    assert target.exists(), "HABITS_DB must choose the database file"


def test_verbose_logs_key_value_to_stderr(db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--db", str(db), "--today", TODAY, "-v", "add", "Read"]) == 0
    captured = capsys.readouterr()
    assert captured.out == "created read (daily)\n", "stdout carries only the result"
    assert "event='habit_created'" in captured.err and "habit_id='read'" in captured.err
