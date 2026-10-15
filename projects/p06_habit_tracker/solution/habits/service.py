"""Service layer: the application's use cases, written against ports only."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import replace
from datetime import date, timedelta

import structlog

from habits.domain import (
    Completion,
    Frequency,
    Habit,
    HabitStats,
    ValidationError,
    compute_stats,
    current_streak,
    longest_streak,
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
        self._repo = repository
        self._clock = clock

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
        freq = Frequency.parse(frequency) if isinstance(frequency, str) else frequency
        habit = Habit.create(name, freq, self._clock.today())
        self._repo.add(habit)
        log.info("habit_created", habit_id=habit.id, frequency=str(freq))
        return habit

    def archive_habit(self, habit_id: str) -> Habit:
        """Archive a habit (idempotent).

        Args:
            habit_id: The habit id.

        Returns:
            The archived habit.

        Raises:
            NotFoundError: If the id is unknown.
        """
        habit = self._repo.get(habit_id)
        if not habit.archived:
            habit = replace(habit, archived=True)
            self._repo.update(habit)
            log.info("habit_archived", habit_id=habit_id)
        return habit

    def list_habits(self, *, include_archived: bool = False) -> list[Habit]:
        """Return habits sorted by id.

        Args:
            include_archived: Also return archived habits.

        Returns:
            The habits.
        """
        return self._repo.list_habits(include_archived=include_archived)

    def _check_day(self, habit: Habit, day: date | None) -> date:
        today = self._clock.today()
        when = today if day is None else day
        if when > today:
            raise ValidationError(f"cannot check in on a future date ({when.isoformat()})")
        if when < habit.created_on:
            raise ValidationError(f"{habit.id!r} did not exist yet on {when.isoformat()}")
        return when

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
        habit = self._repo.get(habit_id)
        if habit.archived:
            raise ValidationError(f"{habit_id!r} is archived")
        when = self._check_day(habit, day)
        if not habit.frequency.is_due(when):
            raise ValidationError(f"{habit_id!r} is not due on {when:%A}s")
        period = habit.frequency.period_start(when)
        if any(habit.frequency.period_start(c.day) == period for c in self._repo.completions(habit_id)):
            log.info("check_in_skipped", habit_id=habit_id, day=when.isoformat(), reason="period already done")
            return False
        self._repo.add_completion(Completion(habit_id, when))
        log.info("checked_in", habit_id=habit_id, day=when.isoformat())
        return True

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
        habit = self._repo.get(habit_id)
        when = self._clock.today() if day is None else day
        period = habit.frequency.period_start(when)
        removed = False
        for completion in self._repo.completions(habit_id):
            if habit.frequency.period_start(completion.day) == period:
                removed = self._repo.remove_completion(habit_id, completion.day) or removed
        log.info("check_in_undone", habit_id=habit_id, day=when.isoformat(), removed=removed)
        return removed

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
        habit = self._repo.get(habit_id)
        today = self._clock.today()
        last = today if end is None else end
        first = last - timedelta(days=29) if start is None else start
        if first > last:
            raise ValidationError("start must not be after end")
        return compute_stats(habit, self._repo.completions(habit_id), today, first, last)

    def _export_rows(self, include_archived: bool) -> list[dict[str, object]]:
        today = self._clock.today()
        rows: list[dict[str, object]] = []
        for habit in self._repo.list_habits(include_archived=include_archived):
            done = self._repo.completions(habit.id)
            rows.append(
                {
                    "id": habit.id,
                    "name": habit.name,
                    "frequency": str(habit.frequency),
                    "created_on": habit.created_on.isoformat(),
                    "archived": habit.archived,
                    "completions": [c.day.isoformat() for c in done],
                    "current_streak": current_streak(habit, done, today),
                    "longest_streak": longest_streak(habit, done, today),
                }
            )
        return rows

    def export_json(self, *, include_archived: bool = True) -> str:
        """Export every habit with its check-in dates as a JSON array.

        Args:
            include_archived: Include archived habits.

        Returns:
            Pretty-printed JSON text.
        """
        return json.dumps(self._export_rows(include_archived), indent=2) + "\n"

    def export_csv(self, *, include_archived: bool = True) -> str:
        """Export one CSV row per habit; ``completions`` holds the check-in count.

        Args:
            include_archived: Include archived habits.

        Returns:
            CSV text with a header row.
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in self._export_rows(include_archived):
            dates = row["completions"]
            count = len(dates) if isinstance(dates, list) else 0
            writer.writerow({**row, "completions": count, "archived": str(row["archived"]).lower()})
        return buffer.getvalue()
