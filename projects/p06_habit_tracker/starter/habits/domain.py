"""Domain model: habits, completions, frequency rules, streaks, and completion rates.

Everything in this module is pure: no I/O, no clock, no database. Functions receive the
data they need (including "today") as arguments, which makes them trivial to test.
"""

# Imports the reference solution also uses (add them back as you need them):
#   datetime.timedelta
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
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
        # TODO: WEEKDAYS needs a non-empty set of 0..6; DAILY and WEEKLY must have no weekdays.
        raise NotImplementedError

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
        # TODO: accept 'daily', 'weekly', or names from WEEKDAY_NAMES joined by commas (ignore case/spaces).
        raise NotImplementedError

    def __str__(self) -> str:
        """Return the text form that :meth:`parse` accepts."""
        # TODO: the inverse of parse(): 'daily', 'weekly', or sorted day names like 'mon,wed'.
        raise NotImplementedError

    def period_start(self, day: date) -> date:
        """Return the key of the period that contains ``day``.

        Daily and weekday habits have one-day periods; weekly habits use the Monday of the ISO week.

        Args:
            day: Any date.

        Returns:
            The first date of the period.
        """
        # TODO: weekly periods start on the Monday of the ISO week; other kinds use the day itself.
        raise NotImplementedError

    def is_due(self, day: date) -> bool:
        """Return whether a check-in on ``day`` counts for this frequency.

        Args:
            day: Any date.

        Returns:
            ``False`` only for weekday habits on a day not in their schedule.
        """
        # TODO: only WEEKDAYS habits have days that are not due.
        raise NotImplementedError

    def periods(self, start: date, end: date) -> list[date]:
        """List the due periods that overlap ``start``..``end`` (inclusive), as period keys.

        Args:
            start: First day of the range.
            end: Last day of the range.

        Returns:
            Period keys in ascending order; empty when ``end`` is before ``start``.
        """
        # TODO: return the period keys overlapping start..end; weekly keys are Mondays, step 7 days.
        raise NotImplementedError

    def previous_period(self, key: date) -> date:
        """Return the key of the due period immediately before the period ``key``.

        Args:
            key: A period key.

        Returns:
            The previous due period's key.
        """
        # TODO: step back one week (weekly) or back day by day until a due day (others).
        raise NotImplementedError


_SLUG_INVALID = re.compile("[^a-z0-9]+")


def slugify(name: str) -> str:
    """Turn a habit name into a stable id: lowercase words joined by hyphens.

    Args:
        name: Human-readable habit name.

    Returns:
        The slug, for example ``"drink-water"`` for ``"Drink Water!"``.

    Raises:
        ValidationError: If the name has no letters or digits.
    """
    # TODO: lowercase, replace runs of non [a-z0-9] with '-', strip '-' from the ends; reject empty.
    raise NotImplementedError


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
        # TODO: strip the name, validate 1..80 characters, and use slugify() for the id.
        raise NotImplementedError


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
    # TODO: map each counted completion to frequency.period_start(day); skip early/not-due ones.
    raise NotImplementedError


def _last_due_period(habit: Habit, today: date) -> date:
    # TODO: implement _last_due_period.
    raise NotImplementedError


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
    # TODO: start from the last due period on or before today. If it is today's period and not done yet,
    # TODO: start from the previous period instead (today is still in progress). Count back while satisfied.
    raise NotImplementedError


def longest_streak(habit: Habit, completions: Iterable[Completion], today: date) -> int:
    """Return the longest run of consecutive satisfied periods from creation up to ``today``.

    Args:
        habit: The habit.
        completions: Its completions.
        today: The current date (later check-ins are ignored).

    Returns:
        The best streak length in periods.
    """
    # TODO: walk frequency.periods(created_on, today) and track the longest satisfied run.
    raise NotImplementedError


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
    # TODO: clip start to created_on, then count satisfied periods; rate is 0.0 with no periods.
    raise NotImplementedError


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
    # TODO: combine completion_rate, current_streak, and longest_streak into HabitStats.
    raise NotImplementedError
