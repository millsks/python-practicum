"""SQLite persistence of plans and actual deliveries."""

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self

from routewise.routing import Delivery, Plan, Route

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
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)

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
        stamp = created_at or datetime.now(UTC).isoformat(timespec="seconds")
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO plans (label, method, capacity, created_at) VALUES (?, ?, ?, ?)",
                (label, plan.method, capacity, stamp),
            )
            plan_id = cursor.lastrowid
            assert plan_id is not None
            self._conn.executemany(
                "INSERT INTO plan_stops (plan_id, route_index, position, customer_id) VALUES (?, ?, ?, ?)",
                [(plan_id, r, p, cid) for r, route in enumerate(plan.routes) for p, cid in enumerate(route.stops)],
            )
        return plan_id

    def _require(self, plan_id: int) -> str:
        row = self._conn.execute("SELECT method FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if row is None:
            raise PlanNotFoundError(f"no plan with id {plan_id}")
        return str(row[0])

    def load_plan(self, plan_id: int) -> Plan:
        """Load a stored plan.

        Raises:
            PlanNotFoundError: If the id does not exist.
        """
        method = self._require(plan_id)
        rows = self._conn.execute(
            "SELECT route_index, customer_id FROM plan_stops WHERE plan_id = ? ORDER BY route_index, position",
            (plan_id,),
        ).fetchall()
        routes: dict[int, list[int]] = {}
        for route_index, customer_id in rows:
            routes.setdefault(route_index, []).append(customer_id)
        return Plan(tuple(Route(tuple(routes[i])) for i in sorted(routes)), method)

    def latest_plan_id(self) -> int | None:
        """Return the newest plan id, or ``None`` if the store is empty."""
        row = self._conn.execute("SELECT MAX(id) FROM plans").fetchone()
        return None if row[0] is None else int(row[0])

    def list_plans(self) -> list[PlanSummary]:
        """Summaries of every stored plan, oldest first."""
        rows = self._conn.execute(
            """
            SELECT p.id, p.label, p.method, p.capacity, p.created_at,
                   COUNT(DISTINCT s.route_index), COUNT(s.customer_id)
            FROM plans AS p LEFT JOIN plan_stops AS s ON s.plan_id = p.id
            GROUP BY p.id ORDER BY p.id
            """
        ).fetchall()
        return [PlanSummary(*row) for row in rows]

    def save_deliveries(self, plan_id: int, deliveries: Iterable[Delivery]) -> int:
        """Record actual deliveries for a plan, replacing earlier records for the same customers.

        Returns:
            The number of rows written.

        Raises:
            PlanNotFoundError: If the plan does not exist.
        """
        self._require(plan_id)
        rows = [(plan_id, d.customer, d.van, d.planned_arrival, d.actual_arrival, d.due) for d in deliveries]
        with self._conn:
            self._conn.executemany(
                "INSERT OR REPLACE INTO deliveries "
                "(plan_id, customer_id, van, planned_arrival, actual_arrival, due) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
        return len(rows)

    def load_deliveries(self, plan_id: int) -> list[Delivery]:
        """Deliveries recorded for a plan, ordered by van then planned arrival.

        Raises:
            PlanNotFoundError: If the plan does not exist.
        """
        self._require(plan_id)
        rows = self._conn.execute(
            "SELECT customer_id, van, planned_arrival, actual_arrival, due FROM deliveries "
            "WHERE plan_id = ? ORDER BY van, planned_arrival",
            (plan_id,),
        ).fetchall()
        return [Delivery(*row) for row in rows]
