"""Milestone 1: the pure domain (frequencies, habits, streaks, completion rates)."""

from datetime import date, timedelta

import pytest
from habits.domain import (
    Completion,
    Frequency,
    FrequencyKind,
    Habit,
    ValidationError,
    completion_rate,
    compute_stats,
    current_streak,
    longest_streak,
    slugify,
)

MON = date(2026, 1, 5)  # a Monday


def d(offset: int) -> date:
    return MON + timedelta(days=offset)


def done(habit: Habit, *offsets: int) -> list[Completion]:
    return [Completion(habit.id, d(o)) for o in offsets]


def make(freq: Frequency, created: date = MON) -> Habit:
    return Habit.create("Read", freq, created)


# --- Frequency ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "kind"), [("daily", FrequencyKind.DAILY), ("WEEKLY", FrequencyKind.WEEKLY), (" daily ", "daily")]
)
def test_parse_simple_frequencies(text: str, kind: str) -> None:
    assert Frequency.parse(text).kind == kind, f"{text!r} should parse to {kind}"


def test_parse_weekdays() -> None:
    freq = Frequency.parse("fri, mon,wed")
    assert freq.kind is FrequencyKind.WEEKDAYS
    assert freq.weekdays == frozenset({0, 2, 4}), "mon, wed, fri are weekdays 0, 2, 4"


@pytest.mark.parametrize("text", ["daily", "weekly", "mon,wed,fri", "sun"])
def test_str_round_trips_through_parse(text: str) -> None:
    assert str(Frequency.parse(text)) == text, "str(freq) must be text that parse() accepts"


@pytest.mark.parametrize("text", ["", "hourly", "mon,funday", ","])
def test_parse_rejects_unknown_text(text: str) -> None:
    with pytest.raises(ValidationError):
        Frequency.parse(text)


def test_frequency_validates_weekdays() -> None:
    with pytest.raises(ValidationError):
        Frequency(FrequencyKind.WEEKDAYS)
    with pytest.raises(ValidationError):
        Frequency(FrequencyKind.DAILY, frozenset({1}))
    with pytest.raises(ValidationError):
        Frequency.on(7)


def test_period_start() -> None:
    assert Frequency.weekly().period_start(d(3)) == MON, "a weekly period starts on Monday"
    assert Frequency.weekly().period_start(d(6)) == MON, "Sunday belongs to the same ISO week"
    assert Frequency.daily().period_start(d(3)) == d(3), "a daily period is the day itself"


def test_is_due() -> None:
    freq = Frequency.on(0, 2)
    assert freq.is_due(d(0)) and freq.is_due(d(2))
    assert not freq.is_due(d(1)), "Tuesday is not in mon,wed"
    assert Frequency.daily().is_due(d(1)) and Frequency.weekly().is_due(d(1))


def test_periods_by_kind() -> None:
    assert len(Frequency.daily().periods(d(0), d(6))) == 7
    assert Frequency.weekly().periods(d(2), d(15)) == [d(0), d(7), d(14)], "weeks overlapping the range"
    assert Frequency.on(0, 4).periods(d(0), d(13)) == [d(0), d(4), d(7), d(11)]
    assert Frequency.daily().periods(d(3), d(2)) == [], "an empty range has no periods"


def test_previous_period_skips_days_not_due() -> None:
    assert Frequency.on(0, 4).previous_period(d(7)) == d(4), "before next Monday comes Friday"
    assert Frequency.weekly().previous_period(d(7)) == d(0)
    assert Frequency.daily().previous_period(d(1)) == d(0)


# --- Habit ---------------------------------------------------------------------------------------


def test_slugify() -> None:
    assert slugify("  Drink Water! ") == "drink-water"
    assert slugify("10k steps") == "10k-steps"
    with pytest.raises(ValidationError):
        slugify("!!!")


def test_habit_create_cleans_name() -> None:
    habit = Habit.create("  Morning Run ", Frequency.daily(), MON)
    assert (habit.id, habit.name, habit.archived) == ("morning-run", "Morning Run", False)


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
def test_habit_create_rejects_bad_names(name: str) -> None:
    with pytest.raises(ValidationError):
        Habit.create(name, Frequency.daily(), MON)


def test_habit_is_immutable() -> None:
    habit = make(Frequency.daily())
    with pytest.raises(AttributeError):
        habit.name = "other"  # type: ignore[misc]


# --- Streaks -------------------------------------------------------------------------------------


def test_current_streak_daily_counts_today() -> None:
    habit = make(Frequency.daily())
    assert current_streak(habit, done(habit, 0, 1, 2), today=d(2)) == 3


def test_current_streak_unchecked_today_does_not_break() -> None:
    habit = make(Frequency.daily())
    assert current_streak(habit, done(habit, 0, 1, 2), today=d(3)) == 3, "today is still in progress"


def test_current_streak_broken_by_missed_day() -> None:
    habit = make(Frequency.daily())
    assert current_streak(habit, done(habit, 0, 1, 2), today=d(4)) == 0, "yesterday was missed"
    assert current_streak(habit, done(habit, 0, 2, 3), today=d(3)) == 2


def test_current_streak_weekly() -> None:
    habit = make(Frequency.weekly())
    assert current_streak(habit, done(habit, 1, 9, 20), today=d(20)) == 3, "three consecutive weeks"
    assert current_streak(habit, done(habit, 1, 9), today=d(20)) == 2, "this week is still open"
    assert current_streak(habit, done(habit, 1), today=d(20)) == 0, "last week was missed"


def test_current_streak_weekdays_on_rest_day() -> None:
    habit = make(Frequency.on(0, 2, 4))
    assert current_streak(habit, done(habit, 0, 2, 4), today=d(5)) == 3, "Saturday is not due"
    assert current_streak(habit, done(habit, 0, 2), today=d(5)) == 0, "Friday was missed"


def test_longest_streak() -> None:
    habit = make(Frequency.daily())
    completions = done(habit, 0, 1, 2, 3, 5, 6)
    assert longest_streak(habit, completions, today=d(10)) == 4
    assert longest_streak(habit, [], today=d(10)) == 0


def test_streaks_ignore_early_and_not_due_check_ins() -> None:
    habit = make(Frequency.on(0), created=d(7))
    completions = [*done(habit, 0, 1, 7, 8), Completion("other", d(14))]
    assert longest_streak(habit, completions, today=d(14)) == 1, "only Monday d(7) counts"


# --- Completion rate ------------------------------------------------------------------------------


def test_completion_rate_daily() -> None:
    habit = make(Frequency.daily())
    assert completion_rate(habit, done(habit, 0, 2, 4, 6), d(0), d(7)) == (4, 8, 0.5)


def test_completion_rate_clips_to_creation() -> None:
    habit = make(Frequency.daily(), created=d(5))
    completed, periods, rate = completion_rate(habit, done(habit, 5, 6), d(0), d(6))
    assert (completed, periods) == (2, 2), "days before creation are not periods"
    assert rate == 1.0


def test_completion_rate_without_periods_is_zero() -> None:
    habit = make(Frequency.on(0))
    assert completion_rate(habit, [], d(1), d(3)) == (0, 0, 0.0), "no Mondays in range"


def test_compute_stats() -> None:
    habit = make(Frequency.daily())
    stats = compute_stats(habit, done(habit, 0, 1, 3, 4), today=d(4), start=d(0), end=d(4))
    assert (stats.current_streak, stats.longest_streak, stats.completed, stats.periods) == (2, 2, 4, 5)
    assert stats.completion_rate == pytest.approx(0.8)
