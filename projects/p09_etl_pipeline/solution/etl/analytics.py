"""Analytics queries over the star schema, written with CTEs and window functions."""

import sqlite3
from dataclasses import dataclass

DAILY_TRIPS_SQL = """
WITH daily AS (
    SELECT d.date AS day, COUNT(*) AS trips
    FROM fact_trip AS f
    JOIN dim_date AS d ON d.date_key = f.date_key
    GROUP BY d.date
)
SELECT day,
       trips,
       ROUND(AVG(trips) OVER (ORDER BY day ROWS BETWEEN :span PRECEDING AND CURRENT ROW), 2) AS moving_avg
FROM daily
ORDER BY day
"""

TOP_ROUTES_SQL = """
WITH routes AS (
    SELECT s1.station_id AS start_id, s2.station_id AS end_id, COUNT(*) AS trips
    FROM fact_trip AS f
    JOIN dim_station AS s1 ON s1.station_key = f.start_station_key
    JOIN dim_station AS s2 ON s2.station_key = f.end_station_key
    GROUP BY s1.station_id, s2.station_id
),
ranked AS (
    SELECT r.*, RANK() OVER (ORDER BY r.trips DESC) AS route_rank
    FROM routes AS r
)
SELECT cs.name AS start_name, ce.name AS end_name, ranked.trips, ranked.route_rank
FROM ranked
JOIN dim_station AS cs ON cs.station_id = ranked.start_id AND cs.is_current = 1
JOIN dim_station AS ce ON ce.station_id = ranked.end_id AND ce.is_current = 1
ORDER BY ranked.trips DESC, start_name, end_name
LIMIT :limit
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
    if window < 1:
        raise ValueError("window must be at least 1")
    rows = conn.execute(DAILY_TRIPS_SQL, {"span": window - 1})
    return [DailyTrips(day, trips, avg) for day, trips, avg in rows]


def top_routes(conn: sqlite3.Connection, limit: int = 5) -> list[Route]:
    """Most-travelled (start, end) station pairs, labelled with current station names.

    Routes are grouped by natural station id, so a renamed station's history counts as one route.

    Args:
        conn: Warehouse connection.
        limit: Maximum rows.

    Returns:
        Routes ordered by trips descending, then names.
    """
    rows = conn.execute(TOP_ROUTES_SQL, {"limit": limit})
    return [Route(a, b, trips, rank) for a, b, trips, rank in rows]
