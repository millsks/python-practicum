"""In-memory adapter for :class:`habits.ports.HabitRepository`, ideal for tests and demos."""

from datetime import date

from habits.domain import Completion, DuplicateHabitError, Habit, NotFoundError


class InMemoryRepository:
    """Keep habits and completions in dictionaries; nothing survives the process."""

    def __init__(self) -> None:
        """Create an empty repository."""
        self._habits: dict[str, Habit] = {}
        self._completions: dict[str, set[date]] = {}

    def add(self, habit: Habit) -> None:
        """Store a new habit.

        Args:
            habit: The habit to store.

        Raises:
            DuplicateHabitError: If a habit with the same id exists.
        """
        if habit.id in self._habits:
            raise DuplicateHabitError(f"habit {habit.id!r} already exists")
        self._habits[habit.id] = habit
        self._completions[habit.id] = set()

    def get(self, habit_id: str) -> Habit:
        """Return one habit.

        Args:
            habit_id: The habit id.

        Returns:
            The habit.

        Raises:
            NotFoundError: If the id is unknown.
        """
        try:
            return self._habits[habit_id]
        except KeyError:
            raise NotFoundError(f"no habit {habit_id!r}") from None

    def list_habits(self, *, include_archived: bool = False) -> list[Habit]:
        """Return habits sorted by id.

        Args:
            include_archived: Also return archived habits.

        Returns:
            The habits.
        """
        return [h for _, h in sorted(self._habits.items()) if include_archived or not h.archived]

    def update(self, habit: Habit) -> None:
        """Replace a stored habit.

        Args:
            habit: The new version.

        Raises:
            NotFoundError: If the id is unknown.
        """
        self.get(habit.id)
        self._habits[habit.id] = habit

    def add_completion(self, completion: Completion) -> bool:
        """Record a check-in.

        Args:
            completion: The check-in.

        Returns:
            ``True`` if stored, ``False`` if it was already recorded.

        Raises:
            NotFoundError: If the habit is unknown.
        """
        self.get(completion.habit_id)
        days = self._completions[completion.habit_id]
        if completion.day in days:
            return False
        days.add(completion.day)
        return True

    def remove_completion(self, habit_id: str, day: date) -> bool:
        """Delete a check-in.

        Args:
            habit_id: The habit id.
            day: The day of the check-in.

        Returns:
            ``True`` if a check-in was removed.
        """
        days = self._completions.get(habit_id, set())
        if day not in days:
            return False
        days.remove(day)
        return True

    def completions(self, habit_id: str) -> list[Completion]:
        """Return a habit's check-ins sorted by day.

        Args:
            habit_id: The habit id.

        Returns:
            The check-ins.
        """
        return [Completion(habit_id, d) for d in sorted(self._completions.get(habit_id, set()))]
