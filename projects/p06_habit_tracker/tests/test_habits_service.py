"""Milestone 3: the service layer, driven by a fake clock and the in-memory repository."""

import csv
import io
import json
from datetime import date, timedelta

import pytest
from habits.domain import DuplicateHabitError, Frequency, NotFoundError, ValidationError
from habits.memory import InMemoryRepository
from habits.ports import FixedClock
from habits.service import EXPORT_FIELDS, HabitService

MON = date(2026, 1, 5)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(MON)


@pytest.fixture
def service(clock: FixedClock) -> HabitService:
    return HabitService(InMemoryRepository(), clock)


def test_fixed_clock_advances(clock: FixedClock) -> None:
    clock.advance(3)
    assert clock.today() == MON + timedelta(days=3)


def test_create_uses_clock_and_slug(service: HabitService) -> None:
    habit = service.create_habit("Drink Water", Frequency.daily())
    assert (habit.id, habit.created_on) == ("drink-water", MON), "created_on comes from the injected clock"


def test_create_accepts_frequency_text(service: HabitService) -> None:
    assert service.create_habit("Gym", "mon,thu").frequency == Frequency.on(0, 3)


def test_create_duplicate_raises(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    with pytest.raises(DuplicateHabitError):
        service.create_habit("READ", "weekly")


def test_check_in_is_idempotent_per_day(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    assert service.check_in("read") is True
    assert service.check_in("read") is False, "a second check-in in the same period is a no-op"


def test_weekly_check_in_once_per_week(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Review", "weekly")
    assert service.check_in("review") is True
    clock.advance(2)
    assert service.check_in("review") is False, "Wednesday is in the same week as Monday"
    clock.advance(5)
    assert service.check_in("review") is True, "next Monday starts a new period"


def test_check_in_backfill(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Read", "daily")
    clock.advance(3)
    assert service.check_in("read", MON + timedelta(days=1)) is True
    assert service.stats("read").completed == 1


@pytest.mark.parametrize("offset", [1, -1])
def test_check_in_rejects_future_and_pre_creation(service: HabitService, offset: int) -> None:
    service.create_habit("Read", "daily")
    with pytest.raises(ValidationError):
        service.check_in("read", MON + timedelta(days=offset))


def test_check_in_rejects_day_not_due(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Gym", "mon,wed")
    clock.advance(1)
    with pytest.raises(ValidationError, match="not due"):
        service.check_in("gym")


def test_check_in_rejects_archived(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    service.archive_habit("read")
    with pytest.raises(ValidationError, match="archived"):
        service.check_in("read")


def test_unknown_habit_raises_not_found(service: HabitService) -> None:
    for call in (service.check_in, service.undo, service.archive_habit, service.stats):
        with pytest.raises(NotFoundError):
            call("ghost")


def test_undo(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    service.check_in("read")
    assert service.undo("read") is True
    assert service.undo("read") is False, "nothing left to undo"
    assert service.check_in("read") is True, "after undo the period is open again"


def test_undo_weekly_from_any_day_of_the_week(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Review", "weekly")
    service.check_in("review")
    clock.advance(4)
    assert service.undo("review") is True, "Friday's undo clears Monday's check-in in the same week"


def test_archive_is_idempotent_and_hides(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    service.create_habit("Walk", "daily")
    assert service.archive_habit("read").archived
    assert service.archive_habit("read").archived
    assert [h.id for h in service.list_habits()] == ["walk"]
    assert len(service.list_habits(include_archived=True)) == 2


def test_stats_over_several_days(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Read", "daily")
    for _ in range(3):
        service.check_in("read")
        clock.advance()
    clock.advance()
    service.check_in("read")
    stats = service.stats("read")
    assert (stats.current_streak, stats.longest_streak) == (1, 3)
    assert (stats.completed, stats.periods) == (4, 5), "default window is clipped to the creation date"


def test_stats_explicit_window(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Read", "daily")
    service.check_in("read")
    clock.advance(9)
    stats = service.stats("read", MON, MON + timedelta(days=1))
    assert stats.completion_rate == 0.5


def test_stats_rejects_reversed_window(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    with pytest.raises(ValidationError):
        service.stats("read", MON, MON - timedelta(days=1))


def test_export_json(service: HabitService, clock: FixedClock) -> None:
    service.create_habit("Read", "daily")
    service.check_in("read")
    clock.advance()
    service.check_in("read")
    data = json.loads(service.export_json())
    assert data == [
        {
            "id": "read",
            "name": "Read",
            "frequency": "daily",
            "created_on": "2026-01-05",
            "archived": False,
            "completions": ["2026-01-05", "2026-01-06"],
            "current_streak": 2,
            "longest_streak": 2,
        }
    ]


def test_export_csv(service: HabitService) -> None:
    service.create_habit("Read", "daily")
    service.create_habit("Walk", "weekly")
    service.archive_habit("walk")
    service.check_in("read")
    rows = list(csv.DictReader(io.StringIO(service.export_csv())))
    assert tuple(rows[0]) == EXPORT_FIELDS, "header must list the export fields in order"
    assert [(r["id"], r["completions"], r["archived"]) for r in rows] == [("read", "1", "false"), ("walk", "0", "true")]
    assert len(list(csv.DictReader(io.StringIO(service.export_csv(include_archived=False))))) == 1
