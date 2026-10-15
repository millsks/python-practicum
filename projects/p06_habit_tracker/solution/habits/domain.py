"""Domain model: habits, completions, frequency rules, streaks, and completion rates.

Everything in this module is pure: no I/O, no clock, no database. Functions receive the
data they need (including "today") as arguments, which makes them trivial to test.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import StrEnum

WEEKDAY_NAMES: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class HabitError(Exception):
    """Base class for every error the habit tracker raises on purpose."""


class ValidationError(HabitError):
    """Raised when input breaks a domain rule (bad name, bad date, archived habit, ...)."""


class NotFoundError(HabitError):
    """Raised when a habit id does not exist."""


class DuplicateHabitError(HabitError):
    """Raised when a habit with the same id already exists."""


class FrequencyKind(StrEnum):
    """How often a habit is due."""

    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"


@dataclass(frozen=True, slots=True)
class Frequency:
    """A habit's schedule.

    Attributes:
        kind: Daily, weekly (once per ISO week), or on specific weekdays.
        weekdays: For ``WEEKDAYS``, the due days as ``date.weekday()`` numbers (Monday is 0).
    """

    kind: FrequencyKind
    weekdays: frozenset[int] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        """Validate that ``weekdays`` matches ``kind``.

        Raises:
            ValidationError: If the weekdays are missing, unexpected, or out of range.
        """
        if self.kind is FrequencyKind.WEEKDAYS:
            if not self.weekdays:
                raise ValidationError("a weekdays frequency needs at least one day")
            if not all(0 <= d <= 6 for d in self.weekdays):
                raise ValidationError(f"weekdays must be 0..6, got {sorted(self.weekdays)}")
        elif self.weekdays:
            raise ValidationError(f"{self.kind} frequency does not take weekdays")

    @classmethod
    def daily(cls) -> Frequency:
        """Return a daily frequency."""
        return cls(FrequencyKind.DAILY)

    @classmethod
    def weekly(cls) -> Frequency:
        """Return a once-per-ISO-week frequency."""
        return cls(FrequencyKind.WEEKLY)

    @classmethod
    def on(cls, *days: int) -> Frequency:
        """Return a frequency due on the given weekdays.

        Args:
            *days: Weekday numbers, Monday is 0.

        Returns:
            The frequency.
        """
        return cls(FrequencyKind.WEEKDAYS, frozenset(days))

    @classmethod
    def parse(cls, text: str) -> Frequency:
        """Parse ``"daily"``, ``"weekly"``, or a comma-separated weekday list such as ``"mon,wed,fri"``.

        Args:
            text: The frequency text (case-insensitive).

        Returns:
            The parsed frequency.

        Raises:
            ValidationError: If the text is not a recognized frequency.
        """
        cleaned = text.strip().lower()
        if cleaned == FrequencyKind.DAILY:
            return cls.daily()
        if cleaned == FrequencyKind.WEEKLY:
            return cls.weekly()
        names = [part.strip() for part in cleaned.split(",") if part.strip()]
        unknown = [n for n in names if n not in WEEKDAY_NAMES]
        if not names or unknown:
            raise ValidationError(f"unknown frequency {text!r}; use daily, weekly, or days like mon,wed,fri")
        return cls.on(*(WEEKDAY_NAMES.index(n) for n in names))

    def __str__(self) -> str:
        """Return the text form that :meth:`parse` accepts."""
        if self.kind is FrequencyKind.WEEKDAYS:
            return ",".join(WEEKDAY_NAMES[d] for d in sorted(self.weekdays))
        return str(self.kind)

    def period_start(self, day: date) -> date:
        """Return the key of the period that contains ``day``.

        Daily and weekday habits have one-day periods; weekly habits use the Monday of the ISO week.

        Args:
            day: Any date.

        Returns:
            The first date of the period.
        """
        if self.kind is FrequencyKind.WEEKLY:
            return day - timedelta(days=day.weekday())
        return day

    def is_due(self, day: date) -> bool:
        """Return whether a check-in on ``day`` counts for this frequency.

        Args:
            day: Any date.

        Returns:
            ``False`` only for weekday habits on a day not in their schedule.
        """
        return self.kind is not FrequencyKind.WEEKDAYS or day.weekday() in self.weekdays

    def periods(self, start: date, end: date) -> list[date]:
        """List the due periods that overlap ``start``..``end`` (inclusive), as period keys.

        Args:
            start: First day of the range.
            end: Last day of the range.

        Returns:
            Period keys in ascending order; empty when ``end`` is before ``start``.
        """
        if end < start:
            return []
        if self.kind is FrequencyKind.WEEKLY:
            first = self.period_start(start)
            return [first + timedelta(weeks=i) for i in range((end - first).days // 7 + 1)]
        days = (start + timedelta(days=i) for i in range((end - start).days + 1))
        return [d for d in days if self.is_due(d)]

    def previous_period(self, key: date) -> date:
        """Return the key of the due period immediately before the period ``key``.

        Args:
            key: A period key.

        Returns:
            The previous due period's key.
        """
        if self.kind is FrequencyKind.WEEKLY:
            return key - timedelta(weeks=1)
        day = key - timedelta(days=1)
        while not self.is_due(day):
            day -= timedelta(days=1)
        return day


_SLUG_INVALID = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Turn a habit name into a stable id: lowercase words joined by hyphens.

    Args:
        name: Human-readable habit name.

    Returns:
        The slug, for example ``"drink-water"`` for ``"Drink Water!"``.

    Raises:
        ValidationError: If the name has no letters or digits.
    """
    slug = _SLUG_INVALID.sub("-", name.lower()).strip("-")
    if not slug:
        raise ValidationError(f"habit name {name!r} needs at least one letter or digit")
    return slug


@dataclass(frozen=True, slots=True)
class Habit:
    """A habit the user wants to build.

    Attributes:
        id: Stable slug derived from the name.
        name: Display name.
        frequency: When the habit is due.
        created_on: First day the habit exists; earlier periods never count.
        archived: Archived habits are hidden from lists and refuse check-ins.
    """

    id: str
    name: str
    frequency: Frequency
    created_on: date
    archived: bool = False

    @classmethod
    def create(cls, name: str, frequency: Frequency, created_on: date) -> Habit:
        """Build a new habit, validating and slugifying its name.

        Args:
            name: Display name (surrounding whitespace is removed).
            frequency: When the habit is due.
            created_on: Creation date.

        Returns:
            The new, unarchived habit.

        Raises:
            ValidationError: If the name is empty or longer than 80 characters.
        """
        cleaned = name.strip()
        if not cleaned:
            raise ValidationError("habit name must not be empty")
        if len(cleaned) > 80:
            raise ValidationError("habit name must be at most 80 characters")
        return cls(slugify(cleaned), cleaned, frequency, created_on)


@dataclass(frozen=True, slots=True, order=True)
class Completion:
    """One check-in.

    Attributes:
        habit_id: The habit that was done.
        day: The day it was done.
    """

    habit_id: str
    day: date


@dataclass(frozen=True, slots=True)
class HabitStats:
    """Summary numbers for one habit over a date range.

    Attributes:
        habit_id: The habit.
        current_streak: Consecutive satisfied periods ending now.
        longest_streak: Best run of consecutive satisfied periods ever.
        periods: Due periods in the range.
        completed: Satisfied periods in the range.
        completion_rate: ``completed / periods`` (0.0 when there are no periods).
    """

    habit_id: str
    current_streak: int
    longest_streak: int
    periods: int
    completed: int
    completion_rate: float


def satisfied_periods(habit: Habit, completions: Iterable[Completion]) -> set[date]:
    """Return the period keys that have at least one counted check-in.

    Check-ins before the habit was created or on days that are not due are ignored.

    Args:
        habit: The habit.
        completions: Its completions (others are ignored).

    Returns:
        The satisfied period keys.
    """
    freq = habit.frequency
    first = freq.period_start(habit.created_on)
    return {
        freq.period_start(c.day)
        for c in completions
        if c.habit_id == habit.id and freq.is_due(c.day) and freq.period_start(c.day) >= first
    }


def _last_due_period(habit: Habit, today: date) -> date:
    freq = habit.frequency
    key = freq.period_start(today)
    return key if freq.is_due(key) else freq.previous_period(key)


def current_streak(habit: Habit, completions: Iterable[Completion], today: date) -> int:
    """Count consecutive satisfied periods ending at the current period.

    The current period is still in progress, so leaving it unchecked does not break the streak:
    counting then starts from the previous period.

    Args:
        habit: The habit.
        completions: Its completions.
        today: The current date.

    Returns:
        The streak length in periods.
    """
    done = satisfied_periods(habit, completions)
    first = habit.frequency.period_start(habit.created_on)
    key = _last_due_period(habit, today)
    if key not in done and key == habit.frequency.period_start(today):
        key = habit.frequency.previous_period(key)
    streak = 0
    while key >= first and key in done:
        streak += 1
        key = habit.frequency.previous_period(key)
    return streak


def longest_streak(habit: Habit, completions: Iterable[Completion], today: date) -> int:
    """Return the longest run of consecutive satisfied periods from creation up to ``today``.

    Args:
        habit: The habit.
        completions: Its completions.
        today: The current date (later check-ins are ignored).

    Returns:
        The best streak length in periods.
    """
    done = satisfied_periods(habit, completions)
    best = run = 0
    for key in habit.frequency.periods(habit.created_on, today):
        run = run + 1 if key in done else 0
        best = max(best, run)
    return best


def completion_rate(habit: Habit, completions: Iterable[Completion], start: date, end: date) -> tuple[int, int, float]:
    """Measure how many due periods in ``start``..``end`` were satisfied.

    The range is clipped so periods before the habit's creation are not counted.

    Args:
        habit: The habit.
        completions: Its completions.
        start: First day of the range.
        end: Last day of the range.

    Returns:
        ``(completed, periods, rate)`` where ``rate`` is between 0.0 and 1.0.
    """
    done = satisfied_periods(habit, completions)
    periods = habit.frequency.periods(max(start, habit.created_on), end)
    completed = sum(1 for key in periods if key in done)
    return completed, len(periods), (completed / len(periods) if periods else 0.0)


def compute_stats(habit: Habit, completions: Iterable[Completion], today: date, start: date, end: date) -> HabitStats:
    """Compute every statistic for one habit.

    Args:
        habit: The habit.
        completions: Its completions.
        today: The current date, used for streaks.
        start: First day of the completion-rate range.
        end: Last day of the completion-rate range.

    Returns:
        The statistics.
    """
    items = list(completions)
    completed, periods, rate = completion_rate(habit, items, start, end)
    return HabitStats(
        habit_id=habit.id,
        current_streak=current_streak(habit, items, today),
        longest_streak=longest_streak(habit, items, today),
        periods=periods,
        completed=completed,
        completion_rate=rate,
    )
