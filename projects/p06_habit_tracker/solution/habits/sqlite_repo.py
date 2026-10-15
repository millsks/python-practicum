"""SQLite adapter for :class:`habits.ports.HabitRepository`.

Highlights: versioned schema migrations recorded in a ``schema_version`` table, one transaction per
write (``with self._conn:`` commits on success and rolls back on error), and parameterized queries
everywhere so user input is never pasted into SQL.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from types import TracebackType

import structlog

from habits.domain import Completion, DuplicateHabitError, Frequency, Habit, NotFoundError

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
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_version'").fetchone()
    if exists is None:
        return 0
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    return int(row[0]) if row else 0


def migrate(conn: sqlite3.Connection) -> int:
    """Apply every pending migration, each in its own transaction.

    Args:
        conn: An open connection.

    Returns:
        The schema version after migrating.
    """
    with conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        if conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == 0:
            conn.execute("INSERT INTO schema_version (version) VALUES (0)")
    current = schema_version(conn)
    for version in range(current, LATEST_VERSION):
        with conn:
            conn.execute("BEGIN")  # DDL does not open a transaction implicitly; make the upgrade atomic
            for statement in MIGRATIONS[version]:
                conn.execute(statement)
            conn.execute("UPDATE schema_version SET version = ?", (version + 1,))
        log.info("schema_migrated", version=version + 1)
    return schema_version(conn)


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

    def __init__(self, path: str | Path = ":memory:") -> None:
        """Open the database and bring its schema up to date."""
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.version = migrate(self._conn)

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
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO habits (id, name, frequency, created_on, archived) VALUES (?, ?, ?, ?, ?)",
                    (habit.id, habit.name, str(habit.frequency), habit.created_on.isoformat(), int(habit.archived)),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateHabitError(f"habit {habit.id!r} already exists") from exc

    def get(self, habit_id: str) -> Habit:
        """Return one habit.

        Args:
            habit_id: The habit id.

        Returns:
            The habit.

        Raises:
            NotFoundError: If the id is unknown.
        """
        row = self._conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"no habit {habit_id!r}")
        return _row_to_habit(row)

    def list_habits(self, *, include_archived: bool = False) -> list[Habit]:
        """Return habits sorted by id.

        Args:
            include_archived: Also return archived habits.

        Returns:
            The habits.
        """
        sql = "SELECT * FROM habits" + ("" if include_archived else " WHERE archived = 0") + " ORDER BY id"
        return [_row_to_habit(row) for row in self._conn.execute(sql)]

    def update(self, habit: Habit) -> None:
        """Replace a stored habit.

        Args:
            habit: The new version.

        Raises:
            NotFoundError: If the id is unknown.
        """
        with self._conn:
            cursor = self._conn.execute(
                "UPDATE habits SET name = ?, frequency = ?, created_on = ?, archived = ? WHERE id = ?",
                (habit.name, str(habit.frequency), habit.created_on.isoformat(), int(habit.archived), habit.id),
            )
        if cursor.rowcount == 0:
            raise NotFoundError(f"no habit {habit.id!r}")

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
        with self._conn:
            cursor = self._conn.execute(
                "INSERT OR IGNORE INTO completions (habit_id, day) VALUES (?, ?)",
                (completion.habit_id, completion.day.isoformat()),
            )
        return cursor.rowcount == 1

    def remove_completion(self, habit_id: str, day: date) -> bool:
        """Delete a check-in.

        Args:
            habit_id: The habit id.
            day: The day of the check-in.

        Returns:
            ``True`` if a check-in was removed.
        """
        with self._conn:
            cursor = self._conn.execute(
                "DELETE FROM completions WHERE habit_id = ? AND day = ?", (habit_id, day.isoformat())
            )
        return cursor.rowcount == 1

    def completions(self, habit_id: str) -> list[Completion]:
        """Return a habit's check-ins sorted by day.

        Args:
            habit_id: The habit id.

        Returns:
            The check-ins.
        """
        rows = self._conn.execute("SELECT day FROM completions WHERE habit_id = ? ORDER BY day", (habit_id,))
        return [Completion(habit_id, date.fromisoformat(row["day"])) for row in rows]
