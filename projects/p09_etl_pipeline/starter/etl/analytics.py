"""Analytics queries over the star schema, written with CTEs and window functions."""

import sqlite3
from dataclasses import dataclass

DAILY_TRIPS_SQL = """
-- TODO: daily trips per dim_date.date with AVG(...) OVER (ORDER BY day ROWS BETWEEN :span PRECEDING AND CURRENT ROW)
SELECT 1
"""

TOP_ROUTES_SQL = """
-- TODO: group by start/end station_id, RANK() OVER (ORDER BY trips DESC), label with current names, LIMIT :limit
SELECT 1
"""


@dataclass(frozen=True, slots=True)
class DailyTrips:
    """One row of the daily trips report.

    Attributes:
        day: ISO date (local business day).
        trips: Trips that started that day.
        moving_avg: Average of ``trips`` over this day and up to ``window - 1`` previous days, rounded to 2 places.
    """

    day: str
    trips: int
    moving_avg: float


@dataclass(frozen=True, slots=True)
class Route:
    """One row of the top routes report.

    Attributes:
        start_name: Current name of the start station.
        end_name: Current name of the end station.
        trips: Trips on this route.
        rank: ``RANK()`` by trip count (ties share a rank).
    """

    start_name: str
    end_name: str
    trips: int
    rank: int


def daily_trips(conn: sqlite3.Connection, window: int = 7) -> list[DailyTrips]:
    """Trips per day with a trailing moving average.

    Args:
        conn: Warehouse connection.
        window: Moving-average window in days (7 gives a weekly average).

    Returns:
        One row per day in date order.

    Raises:
        ValueError: If ``window`` is less than 1.
    """
    # TODO: validate window, run DAILY_TRIPS_SQL with {'span': window - 1}
    raise NotImplementedError


def top_routes(conn: sqlite3.Connection, limit: int = 5) -> list[Route]:
    """Most-travelled (start, end) station pairs, labelled with current station names.

    Routes are grouped by natural station id, so a renamed station's history counts as one route.

    Args:
        conn: Warehouse connection.
        limit: Maximum rows.

    Returns:
        Routes ordered by trips descending, then names.
    """
    # TODO: run TOP_ROUTES_SQL with {'limit': limit}
    raise NotImplementedError
