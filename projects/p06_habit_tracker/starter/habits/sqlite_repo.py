"""SQLite adapter for :class:`habits.ports.HabitRepository`.

Highlights: versioned schema migrations recorded in a ``schema_version`` table, one transaction per
write (``with self._conn:`` commits on success and rolls back on error), and parameterized queries
everywhere so user input is never pasted into SQL.
"""

# Imports the reference solution also uses (add them back as you need them):
#   habits.domain.DuplicateHabitError, habits.domain.NotFoundError
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from types import TracebackType

import structlog

from habits.domain import Completion, Frequency, Habit

log = structlog.get_logger(__name__)

MIGRATIONS: tuple[tuple[str, ...], ...] = (
    (
        """CREATE TABLE habits (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            frequency TEXT NOT NULL,
            created_on TEXT NOT NULL,
            archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1))
        )""",
        """CREATE TABLE completions (
            habit_id TEXT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            day TEXT NOT NULL,
            PRIMARY KEY (habit_id, day)
        )""",
    ),
    ("CREATE INDEX idx_habits_archived ON habits(archived)",),
)
"""Each entry is one schema version; entry ``i`` upgrades the schema from version ``i`` to ``i + 1``."""

LATEST_VERSION = len(MIGRATIONS)


def schema_version(conn: sqlite3.Connection) -> int:
    """Return the schema version recorded in ``conn`` (0 for a brand-new database).

    Args:
        conn: An open connection.

    Returns:
        The current version.
    """
    # TODO: return 0 if the schema_version table does not exist, else its single version value.
    raise NotImplementedError


def migrate(conn: sqlite3.Connection) -> int:
    """Apply every pending migration, each in its own transaction.

    Args:
        conn: An open connection.

    Returns:
        The schema version after migrating.
    """
    # TODO: create schema_version (one row, version 0) if missing, then for each pending MIGRATIONS entry run its
    # TODO: statements and bump the version inside ONE transaction (with conn: + an explicit BEGIN).
    raise NotImplementedError


def _row_to_habit(row: sqlite3.Row) -> Habit:
    return Habit(
        id=row["id"],
        name=row["name"],
        frequency=Frequency.parse(row["frequency"]),
        created_on=date.fromisoformat(row["created_on"]),
        archived=bool(row["archived"]),
    )


class SqliteRepository:
    """Store habits in a SQLite database file (or ``":memory:"``).

    Args:
        path: Database file path, or ``":memory:"`` for a private in-memory database.
    """

    _conn: sqlite3.Connection
    version: int

    def __init__(self, path: str | Path = ":memory:") -> None:
        """Open the database and bring its schema up to date."""
        # TODO: sqlite3.connect(path), set row_factory = sqlite3.Row, run "PRAGMA foreign_keys = ON",
        # TODO: then self.version = migrate(self._conn).
        raise NotImplementedError

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

    def __enter__(self) -> SqliteRepository:
        """Return ``self`` so the repository works in a ``with`` block."""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        """Close the connection when the ``with`` block ends."""
        self.close()

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
