"""Milestone 2: repository adapters. The contract tests run against both adapters."""

import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from habits.domain import Completion, DuplicateHabitError, Frequency, Habit, NotFoundError
from habits.memory import InMemoryRepository
from habits.ports import HabitRepository
from habits.sqlite_repo import LATEST_VERSION, MIGRATIONS, SqliteRepository, migrate, schema_version

DAY = date(2026, 1, 5)


def habit(name: str, freq: Frequency | None = None) -> Habit:
    return Habit.create(name, freq or Frequency.daily(), DAY)


@pytest.fixture(params=["memory", "sqlite"])
def repo(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[HabitRepository]:
    if request.param == "memory":
        yield InMemoryRepository()
    else:
        with SqliteRepository(tmp_path / "habits.db") as sqlite_repo:
            yield sqlite_repo


# --- Contract: every adapter must pass these ------------------------------------------------------


def test_add_and_get_round_trip(repo: HabitRepository) -> None:
    original = habit("Stretch", Frequency.on(1, 3))
    repo.add(original)
    assert repo.get("stretch") == original, "get() must return an equal Habit, frequency included"


def test_get_unknown_raises(repo: HabitRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.get("nope")


def test_add_duplicate_raises(repo: HabitRepository) -> None:
    repo.add(habit("Read"))
    with pytest.raises(DuplicateHabitError):
        repo.add(habit("read"))


def test_list_sorted_and_hides_archived(repo: HabitRepository) -> None:
    for name in ("Walk", "Code", "Meditate"):
        repo.add(habit(name))
    repo.update(replace(repo.get("meditate"), archived=True))
    assert [h.id for h in repo.list_habits()] == ["code", "walk"], "archived habits are hidden by default"
    assert [h.id for h in repo.list_habits(include_archived=True)] == ["code", "meditate", "walk"]


def test_update_persists(repo: HabitRepository) -> None:
    repo.add(habit("Read"))
    repo.update(replace(repo.get("read"), name="Read books", frequency=Frequency.weekly()))
    stored = repo.get("read")
    assert (stored.name, stored.frequency) == ("Read books", Frequency.weekly())


def test_update_unknown_raises(repo: HabitRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.update(habit("Ghost"))


def test_add_completion_reports_duplicates(repo: HabitRepository) -> None:
    repo.add(habit("Read"))
    assert repo.add_completion(Completion("read", DAY)) is True
    assert repo.add_completion(Completion("read", DAY)) is False, "the same day twice is not stored twice"
    assert len(repo.completions("read")) == 1


def test_add_completion_for_unknown_habit_raises(repo: HabitRepository) -> None:
    with pytest.raises(NotFoundError):
        repo.add_completion(Completion("ghost", DAY))


def test_completions_sorted_by_day(repo: HabitRepository) -> None:
    repo.add(habit("Read"))
    for day in (date(2026, 1, 9), date(2026, 1, 6), date(2026, 1, 7)):
        repo.add_completion(Completion("read", day))
    assert [c.day.day for c in repo.completions("read")] == [6, 7, 9]


def test_remove_completion(repo: HabitRepository) -> None:
    repo.add(habit("Read"))
    repo.add_completion(Completion("read", DAY))
    assert repo.remove_completion("read", DAY) is True
    assert repo.remove_completion("read", DAY) is False, "removing twice reports nothing removed"
    assert repo.completions("read") == []


def test_completions_unknown_habit_is_empty(repo: HabitRepository) -> None:
    assert repo.completions("ghost") == []
    assert repo.remove_completion("ghost", DAY) is False


def test_completions_are_per_habit(repo: HabitRepository) -> None:
    repo.add(habit("Read"))
    repo.add(habit("Walk"))
    repo.add_completion(Completion("read", DAY))
    assert repo.completions("walk") == [], "one habit's check-ins must not leak into another"
    assert repo.completions("read") == [Completion("read", DAY)]


# --- SQLite specifics ------------------------------------------------------------------------------


def test_new_database_is_fully_migrated(tmp_path: Path) -> None:
    with SqliteRepository(tmp_path / "h.db") as sqlite_repo:
        assert sqlite_repo.version == LATEST_VERSION == len(MIGRATIONS)
    conn = sqlite3.connect(tmp_path / "h.db")
    try:
        assert schema_version(conn) == LATEST_VERSION, "schema_version table must record the latest version"
    finally:
        conn.close()


def test_data_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "h.db"
    with SqliteRepository(path) as first:
        first.add(habit("Read"))
        first.add_completion(Completion("read", DAY))
    with SqliteRepository(path) as second:
        assert second.version == LATEST_VERSION, "reopening must not re-run or skip migrations"
        assert second.completions("read") == [Completion("read", DAY)]


def test_migrates_old_database_forward(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    conn.execute("INSERT INTO schema_version VALUES (1)")
    for statement in MIGRATIONS[0]:
        conn.execute(statement)
    conn.commit()
    assert schema_version(conn) == 1
    assert migrate(conn) == LATEST_VERSION, "migrate() applies only the pending migrations"
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
    conn.close()
    assert "idx_habits_archived" in names


def test_migrate_is_idempotent() -> None:
    conn = sqlite3.connect(":memory:")
    assert migrate(conn) == LATEST_VERSION
    assert migrate(conn) == LATEST_VERSION
    assert conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 1, "exactly one version row"
    conn.close()


def test_parameterized_queries_store_hostile_names(tmp_path: Path) -> None:
    hostile = "Bobby'); DROP TABLE habits;--"
    with SqliteRepository(tmp_path / "h.db") as sqlite_repo:
        sqlite_repo.add(habit(hostile))
        assert sqlite_repo.get("bobby-drop-table-habits").name == hostile
        assert len(sqlite_repo.list_habits()) == 1, "the habits table must still exist"


def test_failed_insert_rolls_back(tmp_path: Path) -> None:
    with SqliteRepository(tmp_path / "h.db") as sqlite_repo:
        sqlite_repo.add(habit("Read"))
        with pytest.raises(DuplicateHabitError):
            sqlite_repo.add(habit("Read"))
        sqlite_repo.add(habit("Walk"))
        assert [h.id for h in sqlite_repo.list_habits()] == ["read", "walk"], "a failed write leaves no residue"


def test_close_releases_connection() -> None:
    sqlite_repo = SqliteRepository()
    sqlite_repo.close()
    with pytest.raises(sqlite3.ProgrammingError):
        sqlite_repo.list_habits()
