"""SQLite persistence of plans and actual deliveries."""

import sqlite3  # noqa: F401
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime  # noqa: F401
from pathlib import Path
from types import TracebackType
from typing import Self

from routewise.routing import Delivery, Plan, Route  # noqa: F401

SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    method TEXT NOT NULL,
    capacity REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plan_stops (
    plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    route_index INTEGER NOT NULL,
    position INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    PRIMARY KEY (plan_id, route_index, position),
    UNIQUE (plan_id, customer_id)
);
CREATE TABLE IF NOT EXISTS deliveries (
    plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL,
    van INTEGER NOT NULL,
    planned_arrival REAL NOT NULL,
    actual_arrival REAL NOT NULL,
    due REAL NOT NULL,
    PRIMARY KEY (plan_id, customer_id)
);
"""


class PlanNotFoundError(LookupError):
    """Raised when a plan id does not exist in the store."""


@dataclass(frozen=True, slots=True)
class PlanSummary:
    """One row of :meth:`Store.list_plans`."""

    id: int
    label: str
    method: str
    capacity: float
    created_at: str
    n_routes: int
    n_stops: int


class Store:
    """A SQLite database of plans and deliveries. Use it as a context manager to close it reliably."""

    def __init__(self, path: Path | str) -> None:
        """Open (and create if needed) the database at ``path``; use ``":memory:"`` for a throwaway store."""
        # TODO: sqlite3.connect, enable foreign keys, executescript(SCHEMA).
        raise NotImplementedError

    def __enter__(self) -> Self:
        """Return the open store."""
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        """Close the connection."""
        self.close()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def save_plan(self, plan: Plan, *, label: str = "", capacity: float = 0.0, created_at: str | None = None) -> int:
        """Insert a plan and its stops in one transaction.

        Args:
            plan: Plan to store.
            label: Free-text label, such as the city name.
            capacity: Van capacity used for planning.
            created_at: ISO timestamp; defaults to now in UTC.

        Returns:
            The new plan id.
        """
        # TODO: insert into plans, then executemany the stops, inside `with self._conn:` (one transaction).
        raise NotImplementedError

    def _require(self, plan_id: int) -> str:
        # TODO: implement this function.
        raise NotImplementedError

    def load_plan(self, plan_id: int) -> Plan:
        """Load a stored plan.

        Raises:
            PlanNotFoundError: If the id does not exist.
        """
        # TODO: implement this function.
        raise NotImplementedError

    def latest_plan_id(self) -> int | None:
        """Return the newest plan id, or ``None`` if the store is empty."""
        # TODO: implement this function.
        raise NotImplementedError

    def list_plans(self) -> list[PlanSummary]:
        """Summaries of every stored plan, oldest first."""
        # TODO: implement this function.
        raise NotImplementedError

    def save_deliveries(self, plan_id: int, deliveries: Iterable[Delivery]) -> int:
        """Record actual deliveries for a plan, replacing earlier records for the same customers.

        Returns:
            The number of rows written.

        Raises:
            PlanNotFoundError: If the plan does not exist.
        """
        # TODO: implement this function.
        raise NotImplementedError

    def load_deliveries(self, plan_id: int) -> list[Delivery]:
        """Deliveries recorded for a plan, ordered by van then planned arrival.

        Raises:
            PlanNotFoundError: If the plan does not exist.
        """
        # TODO: implement this function.
        raise NotImplementedError
