"""Route and plan data model, feasibility checks, construction heuristics, 2-opt, and exact Held-Karp."""

import math  # noqa: F401
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace  # noqa: F401
from itertools import pairwise  # noqa: F401
from typing import Protocol, Self

from routewise.data import DEFAULT_HORIZON, City, Customer
from routewise.graph import DistanceMatrix  # noqa: F401

DEPOT = 0
"""Pseudo customer id that stands for the depot in travel-time lookups."""

MAX_HELD_KARP = 12
"""Largest number of customers :func:`held_karp` accepts (its cost grows as n^2 * 2^n)."""

EPSILON = 1e-9


class InfeasibleCustomerError(ValueError):
    """Raised when a customer cannot be served even by a dedicated van."""


class TravelTimes(Protocol):
    """Anything that can report travel minutes between two road nodes."""

    def cost(self, a: int, b: int) -> float:
        """Return travel minutes from node ``a`` to node ``b``."""
        ...


@dataclass(frozen=True, eq=False)
class Instance:
    """A routing problem: one depot, customers, a travel-time oracle, and van limits.

    Attributes:
        depot: Depot road node.
        customers: Customers keyed by id (ids must be 1 or more).
        travel: Travel-time oracle between road nodes.
        capacity: Crates one van can carry.
        horizon: Minute by which every van must be back at the depot.
        coords: Optional node coordinates, used by the sweep algorithm.
    """

    depot: int
    customers: Mapping[int, Customer]
    travel: TravelTimes
    capacity: float
    horizon: float = DEFAULT_HORIZON
    coords: Mapping[int, tuple[float, float]] = field(default_factory=dict)

    @classmethod
    def from_city(cls, city: City, capacity: float, horizon: float = DEFAULT_HORIZON) -> Self:
        """Build an instance over every customer of ``city`` with a cached distance matrix.

        Args:
            city: City to plan for.
            capacity: Van capacity in crates.
            horizon: End of the working day in minutes.

        Returns:
            The instance.
        """
        # TODO: matrix nodes are the depot plus every customer node; pass city.coords() for sweep.
        raise NotImplementedError

    def node(self, customer_id: int) -> int:
        """Road node of a customer id, or of the depot for :data:`DEPOT`."""
        return self.depot if customer_id == DEPOT else self.customers[customer_id].node

    def time(self, a: int, b: int) -> float:
        """Travel minutes between two customer ids (:data:`DEPOT` for the depot)."""
        return self.travel.cost(self.node(a), self.node(b))

    def subset(self, customer_ids: Iterable[int]) -> Self:
        """Return the same instance restricted to some customers."""
        # TODO: implement this function.
        raise NotImplementedError

    def relaxed(self) -> Self:
        """Return a copy with no capacity, time-window, or horizon limits (a pure travelling-salesman problem)."""
        # TODO: dataclasses.replace each customer with ready=0, due=inf; capacity and horizon inf.
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Route:
    """One van's ordered sequence of customer ids; the depot is implicit at both ends."""

    stops: tuple[int, ...]

    def __post_init__(self) -> None:
        """Coerce ``stops`` to a tuple so routes stay hashable and immutable."""
        object.__setattr__(self, "stops", tuple(self.stops))

    def __len__(self) -> int:
        """Return the number of stops."""
        return len(self.stops)


@dataclass(frozen=True, slots=True)
class Plan:
    """A day's plan: one route per van.

    Attributes:
        routes: Routes, one per van; van ``i`` drives ``routes[i]``.
        method: Name of the algorithm that produced the plan.
    """

    routes: tuple[Route, ...]
    method: str = ""

    def __post_init__(self) -> None:
        """Coerce ``routes`` to a tuple."""
        object.__setattr__(self, "routes", tuple(self.routes))

    def customers(self) -> list[int]:
        """All customer ids in driving order, route by route."""
        # TODO: implement this function.
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Visit:
    """When a van reaches, serves, and leaves one customer."""

    customer: int
    arrival: float
    start: float
    departure: float

    @property
    def wait(self) -> float:
        """Minutes spent waiting for the time window to open."""
        return self.start - self.arrival


@dataclass(frozen=True, slots=True)
class Schedule:
    """The simulated timeline of a route leaving the depot at time zero."""

    visits: tuple[Visit, ...]
    travel_minutes: float
    end_time: float
    load: float
    violations: tuple[str, ...]

    @property
    def feasible(self) -> bool:
        """Whether the route breaks no constraint."""
        return not self.violations

    @property
    def total_wait(self) -> float:
        """Total minutes spent waiting for windows to open."""
        return sum(v.wait for v in self.visits)


@dataclass(frozen=True, slots=True)
class Delivery:
    """A delivery that actually happened, compared with its plan.

    Attributes:
        customer: Customer id.
        van: Index of the route (van) that served the customer.
        planned_arrival: Planned arrival minute.
        actual_arrival: Observed arrival minute.
        due: Latest allowed service start.
    """

    customer: int
    van: int
    planned_arrival: float
    actual_arrival: float
    due: float

    @property
    def on_time(self) -> bool:
        """Whether the van arrived no later than the window closed."""
        return self.actual_arrival <= self.due + EPSILON

    @property
    def delay(self) -> float:
        """Actual minus planned arrival (negative when early)."""
        return self.actual_arrival - self.planned_arrival


def schedule(stops: Route | Sequence[int], inst: Instance, start_time: float = 0.0) -> Schedule:
    """Simulate a route: drive, wait for windows to open, serve, and return to the depot.

    Args:
        stops: A route or a sequence of customer ids.
        inst: Problem instance.
        start_time: Minute the van leaves the depot.

    Returns:
        The timeline plus any constraint violations (capacity, late arrival, horizon, unreachable).

    Raises:
        KeyError: If a stop is not a customer of ``inst``.
    """
    # TODO: clock starts at start_time; arrival = clock + leg; start = max(arrival, ready); late if start > due.
    raise NotImplementedError


def route_cost(stops: Route | Sequence[int], inst: Instance) -> float:
    """Total travel minutes of a route including both depot legs."""
    # TODO: sum travel over (DEPOT, *stops, DEPOT) consecutive pairs (itertools.pairwise).
    raise NotImplementedError


def plan_cost(plan: Plan, inst: Instance) -> float:
    """Total travel minutes over every route of ``plan``."""
    # TODO: implement this function.
    raise NotImplementedError


def check_plan(plan: Plan, inst: Instance) -> list[str]:
    """List every problem with a plan: route violations, unknown, duplicated, or missing customers.

    Args:
        plan: Plan to validate.
        inst: Instance it should solve.

    Returns:
        Human-readable problems; empty when the plan is feasible and serves every customer exactly once.
    """
    # TODO: collect unknown, duplicate, and missing customers plus every route's schedule violations.
    raise NotImplementedError


def is_feasible(plan: Plan, inst: Instance) -> bool:
    """Whether :func:`check_plan` finds no problems."""
    # TODO: implement this function.
    raise NotImplementedError


def _ensure_servable(inst: Instance, customer_ids: Iterable[int]) -> None:
    # TODO: implement this function.
    raise NotImplementedError


def nearest_neighbor(inst: Instance, customers: Iterable[int] | None = None) -> Plan:
    """Greedy construction: repeatedly drive to the nearest customer that keeps the route feasible.

    When no remaining customer fits (capacity, window, or return-by-horizon), the van returns and a new route
    starts. Runs in O(n^2) time.

    Args:
        inst: Problem instance.
        customers: Customer ids to route; defaults to all of them.

    Returns:
        A feasible plan covering the customers.

    Raises:
        InfeasibleCustomerError: If some customer cannot be served on its own.
    """
    # TODO: from the current stop pick the closest customer that keeps the route feasible; else new route.
    raise NotImplementedError


def clarke_wright(inst: Instance, customers: Iterable[int] | None = None) -> Plan:
    """Clarke-Wright parallel savings heuristic.

    Start with one route per customer, then merge route ends in decreasing order of the saving
    ``t(0, i) + t(0, j) - t(i, j)`` whenever the merged route stays feasible.

    Args:
        inst: Problem instance.
        customers: Customer ids to route; defaults to all of them.

    Returns:
        A feasible plan covering the customers, with routes ordered by their first customer id.

    Raises:
        InfeasibleCustomerError: If some customer cannot be served on its own.
    """
    # TODO: savings s_ij = t(0,i) + t(0,j) - t(i,j), largest first; merge route ends if still feasible.
    raise NotImplementedError


def two_opt(route: Route, inst: Instance) -> Route:
    """Improve a route by reversing segments while that shortens it and keeps it feasible.

    Uses first-improvement 2-opt: for each pair of positions, compute the travel-time change of reversing the
    segment between them in O(1); accept the move only if it strictly reduces travel time and the new route is
    feasible (or the original already was not). The result is never longer than the input.

    Args:
        route: Route to improve.
        inst: Problem instance with symmetric travel times.

    Returns:
        The improved route (possibly the same one).
    """
    # TODO: try reversing stops[i..j]; O(1) delta from the four edges; accept only strict, feasible gains.
    raise NotImplementedError


def improve_plan(plan: Plan, inst: Instance) -> Plan:
    """Apply :func:`two_opt` to every route of a plan, dropping empty routes."""
    # TODO: implement this function.
    raise NotImplementedError


def held_karp(inst: Instance, customers: Sequence[int] | None = None) -> tuple[float, tuple[int, ...]]:
    """Exact minimum-travel single route (travelling salesman tour from the depot) by bitmask DP.

    ``best[mask][j]`` is the cheapest way to leave the depot, visit exactly the customers in ``mask``, and end at
    customer ``j``. Capacity and time windows are ignored, which makes this a lower bound for any feasible route over
    the same customers. Time O(n^2 * 2^n), memory O(n * 2^n).

    Args:
        inst: Problem instance.
        customers: Customer ids to visit; defaults to all of them.

    Returns:
        ``(cost, order)`` of an optimal tour.

    Raises:
        ValueError: If more than :data:`MAX_HELD_KARP` customers are given.
    """
    # TODO: best[mask][j] = cheapest path from the depot through mask ending at j; keep parents to rebuild.
    raise NotImplementedError
