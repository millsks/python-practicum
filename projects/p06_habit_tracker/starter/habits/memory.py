"""In-memory adapter for :class:`habits.ports.HabitRepository`, ideal for tests and demos."""

# Imports the reference solution also uses (add them back as you need them):
#   habits.domain.DuplicateHabitError, habits.domain.NotFoundError
from datetime import date

from habits.domain import Completion, Habit


class InMemoryRepository:
    """Keep habits and completions in dictionaries; nothing survives the process."""

    def __init__(self) -> None:
        """Create an empty repository."""
        # TODO: store the collaborators/state this object needs (see the class docstring).
        raise NotImplementedError

    def add(self, habit: Habit) -> None:
        """Store a new habit.

        Args:
            habit: The habit to store.

        Raises:
            DuplicateHabitError: If a habit with the same id exists.
        """
        # TODO: raise DuplicateHabitError if the id exists (SQLite: catch sqlite3.IntegrityError); use ? placeholders.
        raise NotImplementedError

    def get(self, habit_id: str) -> Habit:
        """Return one habit.

        Args:
            habit_id: The habit id.

        Returns:
            The habit.

        Raises:
            NotFoundError: If the id is unknown.
        """
        # TODO: look the habit up by id; raise NotFoundError when it is missing.
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

    def update(self, habit: Habit) -> None:
        """Replace a stored habit.

        Args:
            habit: The new version.

        Raises:
            NotFoundError: If the id is unknown.
        """
        # TODO: replace the stored habit; raise NotFoundError if nothing was updated.
        raise NotImplementedError

    def add_completion(self, completion: Completion) -> bool:
        """Record a check-in.

        Args:
            completion: The check-in.

        Returns:
            ``True`` if stored, ``False`` if it was already recorded.

        Raises:
            NotFoundError: If the habit is unknown.
        """
        # TODO: raise NotFoundError for an unknown habit; return False if (habit_id, day) exists.
        raise NotImplementedError

    def remove_completion(self, habit_id: str, day: date) -> bool:
        """Delete a check-in.

        Args:
            habit_id: The habit id.
            day: The day of the check-in.

        Returns:
            ``True`` if a check-in was removed.
        """
        # TODO: delete the (habit_id, day) check-in and report whether one was removed.
        raise NotImplementedError

    def completions(self, habit_id: str) -> list[Completion]:
        """Return a habit's check-ins sorted by day.

        Args:
            habit_id: The habit id.

        Returns:
            The check-ins.
        """
        # TODO: return Completion objects sorted by day (empty list for an unknown habit).
        raise NotImplementedError
