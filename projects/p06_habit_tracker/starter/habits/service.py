"""Service layer: the application's use cases, written against ports only."""

# Imports the reference solution also uses (add them back as you need them):
#   csv, io, json, dataclasses.replace, datetime.timedelta, habits.domain.Completion, habits.domain.ValidationError, habits.domain.compute_stats, habits.domain.current_streak, habits.domain.longest_streak
from __future__ import annotations

from datetime import date

import structlog

from habits.domain import (
    Frequency,
    Habit,
    HabitStats,
)
from habits.ports import Clock, HabitRepository

log = structlog.get_logger(__name__)

EXPORT_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "frequency",
    "created_on",
    "archived",
    "completions",
    "current_streak",
    "longest_streak",
)


class HabitService:
    """Create, check in, undo, archive, report on, and export habits.

    Args:
        repository: Where habits live.
        clock: Source of "today".
    """

    def __init__(self, repository: HabitRepository, clock: Clock) -> None:
        """Wire the service to its ports."""
        # TODO: store the collaborators/state this object needs (see the class docstring).
        raise NotImplementedError

    def create_habit(self, name: str, frequency: Frequency | str) -> Habit:
        """Create and store a habit that starts today.

        Args:
            name: Display name; its slug becomes the id.
            frequency: A :class:`Frequency` or its text form (``"daily"``, ``"weekly"``, ``"mon,thu"``).

        Returns:
            The stored habit.

        Raises:
            ValidationError: If the name or frequency is invalid.
            DuplicateHabitError: If a habit with the same id exists.
        """
        # TODO: parse text frequencies, build with Habit.create(name, freq, clock.today()), store it, log it.
        raise NotImplementedError

    def archive_habit(self, habit_id: str) -> Habit:
        """Archive a habit (idempotent).

        Args:
            habit_id: The habit id.

        Returns:
            The archived habit.

        Raises:
            NotFoundError: If the id is unknown.
        """
        # TODO: load the habit; if not archived, store dataclasses.replace(habit, archived=True).
        raise NotImplementedError

    def list_habits(self, *, include_archived: bool = False) -> list[Habit]:
        """Return habits sorted by id.

        Args:
            include_archived: Also return archived habits.

        Returns:
            The habits.
        """
        # TODO: return habits sorted by id, skipping archived ones unless include_archived is true.
        raise NotImplementedError

    def _check_day(self, habit: Habit, day: date | None) -> date:
        # TODO: default to today; reject future days and days before habit.created_on.
        raise NotImplementedError

    def check_in(self, habit_id: str, day: date | None = None) -> bool:
        """Record that a habit was done, at most once per period.

        Args:
            habit_id: The habit id.
            day: The day it was done (default today).

        Returns:
            ``True`` if a new check-in was stored, ``False`` if the period was already satisfied.

        Raises:
            NotFoundError: If the id is unknown.
            ValidationError: If the habit is archived, the day is in the future, before creation, or not due.
        """
        # TODO: reject archived habits, future days, days before created_on, and days that are not due.
        # TODO: idempotent per PERIOD: return False if any completion already falls in the same period.
        raise NotImplementedError

    def undo(self, habit_id: str, day: date | None = None) -> bool:
        """Remove the check-in for the period containing ``day``.

        Args:
            habit_id: The habit id.
            day: Any day in the period to undo (default today).

        Returns:
            ``True`` if a check-in was removed.

        Raises:
            NotFoundError: If the id is unknown.
        """
        # TODO: remove every completion whose period_start matches the period containing the day.
        raise NotImplementedError

    def stats(self, habit_id: str, start: date | None = None, end: date | None = None) -> HabitStats:
        """Compute streaks and the completion rate.

        Args:
            habit_id: The habit id.
            start: First day of the rate window (default 29 days before ``end``).
            end: Last day of the rate window (default today).

        Returns:
            The statistics.

        Raises:
            NotFoundError: If the id is unknown.
            ValidationError: If ``start`` is after ``end``.
        """
        # TODO: default window is the 30 days ending today; reject start > end; delegate to compute_stats.
        raise NotImplementedError

    def _export_rows(self, include_archived: bool) -> list[dict[str, object]]:
        # TODO: one dict per habit with the EXPORT_FIELDS keys; completions is a list of ISO dates.
        raise NotImplementedError

    def export_json(self, *, include_archived: bool = True) -> str:
        """Export every habit with its check-in dates as a JSON array.

        Args:
            include_archived: Include archived habits.

        Returns:
            Pretty-printed JSON text.
        """
        # TODO: json.dumps(self._export_rows(...), indent=2) plus a trailing newline.
        raise NotImplementedError

    def export_csv(self, *, include_archived: bool = True) -> str:
        """Export one CSV row per habit; ``completions`` holds the check-in count.

        Args:
            include_archived: Include archived habits.

        Returns:
            CSV text with a header row.
        """
        # TODO: csv.DictWriter with EXPORT_FIELDS; write the completion COUNT and archived as true/false.
        raise NotImplementedError
