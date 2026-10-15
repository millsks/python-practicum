"""Ports: the interfaces the service layer depends on, plus the two clocks.

The service never imports an adapter. It talks to these Protocols, and the CLI (the composition
root) decides which concrete adapter to plug in.
"""

from datetime import date, timedelta
from typing import Protocol

from habits.domain import Completion, Habit


class HabitRepository(Protocol):
    """Storage for habits and their completions."""

    def add(self, habit: Habit) -> None:
        """Store a new habit.

        Args:
            habit: The habit to store.

        Raises:
            DuplicateHabitError: If a habit with the same id exists.
        """
        ...

    def get(self, habit_id: str) -> Habit:
        """Return one habit.

        Args:
            habit_id: The habit id.

        Returns:
            The habit.

        Raises:
            NotFoundError: If the id is unknown.
        """
        ...

    def list_habits(self, *, include_archived: bool = False) -> list[Habit]:
        """Return habits sorted by id.

        Args:
            include_archived: Also return archived habits.

        Returns:
            The habits.
        """
        ...

    def update(self, habit: Habit) -> None:
        """Replace a stored habit with ``habit`` (matched by id).

        Args:
            habit: The new version.

        Raises:
            NotFoundError: If the id is unknown.
        """
        ...

    def add_completion(self, completion: Completion) -> bool:
        """Record a check-in.

        Args:
            completion: The check-in.

        Returns:
            ``True`` if stored, ``False`` if that exact habit and day were already recorded.

        Raises:
            NotFoundError: If the habit is unknown.
        """
        ...

    def remove_completion(self, habit_id: str, day: date) -> bool:
        """Delete a check-in.

        Args:
            habit_id: The habit id.
            day: The day of the check-in.

        Returns:
            ``True`` if a check-in was removed.
        """
        ...

    def completions(self, habit_id: str) -> list[Completion]:
        """Return a habit's check-ins sorted by day.

        Args:
            habit_id: The habit id.

        Returns:
            The check-ins (empty for an unknown habit).
        """
        ...


class Clock(Protocol):
    """Source of the current date."""

    def today(self) -> date:
        """Return the current date."""
        ...


class SystemClock:
    """The real clock, backed by the operating system."""

    def today(self) -> date:
        """Return the local current date."""
        return date.today()


class FixedClock:
    """A controllable clock for tests and for the CLI's ``--today`` option.

    Args:
        day: The date to report.
    """

    def __init__(self, day: date) -> None:
        """Start the clock at ``day``."""
        self._day = day

    def today(self) -> date:
        """Return the configured date."""
        return self._day

    def advance(self, days: int = 1) -> None:
        """Move the clock forward (or backward with a negative number).

        Args:
            days: Days to move.
        """
        self._day += timedelta(days=days)
