"""Route and plan data model, feasibility checks, construction heuristics, 2-opt, and exact Held-Karp."""

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from itertools import pairwise
from typing import Protocol, Self

from routewise.data import DEFAULT_HORIZON, City, Customer
from routewise.graph import DistanceMatrix

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
        nodes = [city.depot, *(c.node for c in city.customers)]
        matrix = DistanceMatrix(city.road_graph(), list(dict.fromkeys(nodes)))
        return cls(city.depot, {c.id: c for c in city.customers}, matrix, capacity, horizon, city.coords())

    def node(self, customer_id: int) -> int:
        """Road node of a customer id, or of the depot for :data:`DEPOT`."""
        return self.depot if customer_id == DEPOT else self.customers[customer_id].node

    def time(self, a: int, b: int) -> float:
        """Travel minutes between two customer ids (:data:`DEPOT` for the depot)."""
        return self.travel.cost(self.node(a), self.node(b))

    def subset(self, customer_ids: Iterable[int]) -> Self:
        """Return the same instance restricted to some customers."""
        return replace(self, customers={cid: self.customers[cid] for cid in customer_ids})

    def relaxed(self) -> Self:
        """Return a copy with no capacity, time-window, or horizon limits (a pure travelling-salesman problem)."""
        open_windows = {cid: replace(c, ready=0.0, due=math.inf) for cid, c in self.customers.items()}
        return replace(self, customers=open_windows, capacity=math.inf, horizon=math.inf)


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
        return [cid for route in self.routes for cid in route.stops]


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
    ids = stops.stops if isinstance(stops, Route) else tuple(stops)
    violations: list[str] = []
    visits: list[Visit] = []
    clock, travel, load, here = start_time, 0.0, 0.0, DEPOT
    for cid in ids:
        customer = inst.customers[cid]
        leg = inst.time(here, cid)
        if math.isinf(leg):
            violations.append(f"customer {cid} is unreachable")
        travel += leg
        arrival = clock + leg
        start = max(arrival, customer.ready)
        if start > customer.due + EPSILON:
            violations.append(f"late at customer {cid}: start {start:.1f} > due {customer.due:.1f}")
        clock = start + customer.service
        visits.append(Visit(cid, arrival, start, clock))
        load += customer.demand
        here = cid
    back = inst.time(here, DEPOT) if ids else 0.0
    travel += back
    clock += back
    if load > inst.capacity + EPSILON:
        violations.append(f"capacity: load {load:g} > {inst.capacity:g}")
    if clock > inst.horizon + EPSILON:
        violations.append(f"returns at {clock:.1f} after horizon {inst.horizon:.1f}")
    return Schedule(tuple(visits), travel, clock, load, tuple(violations))


def route_cost(stops: Route | Sequence[int], inst: Instance) -> float:
    """Total travel minutes of a route including both depot legs."""
    ids = stops.stops if isinstance(stops, Route) else tuple(stops)
    if not ids:
        return 0.0
    path = (DEPOT, *ids, DEPOT)
    return sum(inst.time(a, b) for a, b in pairwise(path))


def plan_cost(plan: Plan, inst: Instance) -> float:
    """Total travel minutes over every route of ``plan``."""
    return sum(route_cost(route, inst) for route in plan.routes)


def check_plan(plan: Plan, inst: Instance) -> list[str]:
    """List every problem with a plan: route violations, unknown, duplicated, or missing customers.

    Args:
        plan: Plan to validate.
        inst: Instance it should solve.

    Returns:
        Human-readable problems; empty when the plan is feasible and serves every customer exactly once.
    """
    problems: list[str] = []
    seen: set[int] = set()
    for index, route in enumerate(plan.routes):
        for cid in route.stops:
            if cid not in inst.customers:
                problems.append(f"route {index}: unknown customer {cid}")
            elif cid in seen:
                problems.append(f"route {index}: customer {cid} visited twice")
            seen.add(cid)
        if all(cid in inst.customers for cid in route.stops):
            problems.extend(f"route {index}: {v}" for v in schedule(route, inst).violations)
    problems.extend(f"customer {cid} is not served" for cid in sorted(set(inst.customers) - seen))
    return problems


def is_feasible(plan: Plan, inst: Instance) -> bool:
    """Whether :func:`check_plan` finds no problems."""
    return not check_plan(plan, inst)


def _ensure_servable(inst: Instance, customer_ids: Iterable[int]) -> None:
    for cid in customer_ids:
        if not schedule((cid,), inst).feasible:
            raise InfeasibleCustomerError(f"customer {cid} cannot be served even by a dedicated van")


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
    remaining = set(inst.customers if customers is None else customers)
    _ensure_servable(inst, remaining)
    routes: list[Route] = []
    while remaining:
        stops: list[int] = []
        clock, load, here = 0.0, 0.0, DEPOT
        while True:
            best: tuple[float, int] | None = None
            for cid in remaining:
                customer = inst.customers[cid]
                leg = inst.time(here, cid)
                start = max(clock + leg, customer.ready)
                fits = load + customer.demand <= inst.capacity + EPSILON and start <= customer.due + EPSILON
                if fits and start + customer.service + inst.time(cid, DEPOT) <= inst.horizon + EPSILON:
                    key = (leg, cid)
                    if best is None or key < best:
                        best = key
            if best is None:
                break
            cid = best[1]
            customer = inst.customers[cid]
            clock = max(clock + inst.time(here, cid), customer.ready) + customer.service
            load += customer.demand
            here = cid
            stops.append(cid)
            remaining.remove(cid)
        routes.append(Route(tuple(stops)))
    return Plan(tuple(routes), "nearest")


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
    ids = sorted(inst.customers if customers is None else customers)
    _ensure_servable(inst, ids)
    routes: dict[int, list[int]] = {cid: [cid] for cid in ids}
    owner = {cid: cid for cid in ids}
    savings = sorted(
        (
            (inst.time(DEPOT, i) + inst.time(DEPOT, j) - inst.time(i, j), i, j)
            for k, i in enumerate(ids)
            for j in ids[k + 1 :]
        ),
        key=lambda s: (-s[0], s[1], s[2]),
    )
    for saving, i, j in savings:
        if saving <= EPSILON:
            break
        ri, rj = owner[i], owner[j]
        if ri == rj:
            continue
        a, b = routes[ri], routes[rj]
        candidates: list[list[int]] = []
        if a[-1] == i and b[0] == j:
            candidates.append(a + b)
        if b[-1] == j and a[0] == i:
            candidates.append(b + a)
        if a[-1] == i and b[-1] == j:
            candidates.append(a + b[::-1])
        if a[0] == i and b[0] == j:
            candidates.append(a[::-1] + b)
        for merged in candidates:
            if schedule(merged, inst).feasible:
                del routes[ri], routes[rj]
                key = min(ri, rj)
                routes[key] = merged
                for cid in merged:
                    owner[cid] = key
                break
    return Plan(tuple(Route(tuple(routes[k])) for k in sorted(routes)), "savings")


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
    best = list(route.stops)
    must_stay_feasible = schedule(best, inst).feasible
    improved = True
    while improved:
        improved = False
        n = len(best)
        for i in range(n - 1):
            before = best[i - 1] if i > 0 else DEPOT
            for j in range(i + 1, n):
                after = best[j + 1] if j + 1 < n else DEPOT
                delta = (
                    inst.time(before, best[j])
                    + inst.time(best[i], after)
                    - inst.time(before, best[i])
                    - inst.time(best[j], after)
                )
                if delta >= -EPSILON:
                    continue
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                if route_cost(candidate, inst) >= route_cost(best, inst) - EPSILON:
                    continue
                if must_stay_feasible and not schedule(candidate, inst).feasible:
                    continue
                best = candidate
                improved = True
                break
            if improved:
                break
    return Route(tuple(best))


def improve_plan(plan: Plan, inst: Instance) -> Plan:
    """Apply :func:`two_opt` to every route of a plan, dropping empty routes."""
    return Plan(tuple(two_opt(r, inst) for r in plan.routes if r.stops), plan.method)


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
    ids = sorted(inst.customers if customers is None else customers)
    n = len(ids)
    if n > MAX_HELD_KARP:
        raise ValueError(f"held_karp is limited to {MAX_HELD_KARP} customers, got {n}")
    if n == 0:
        return 0.0, ()
    t = [[inst.time(a, b) for b in ids] for a in ids]
    full = (1 << n) - 1
    best = [[math.inf] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    for j in range(n):
        best[1 << j][j] = inst.time(DEPOT, ids[j])
    for mask in range(1, full + 1):
        row = best[mask]
        for j in range(n):
            here = row[j]
            if here == math.inf or not mask >> j & 1:
                continue
            for k in range(n):
                if mask >> k & 1:
                    continue
                nxt = mask | 1 << k
                candidate = here + t[j][k]
                if candidate < best[nxt][k]:
                    best[nxt][k] = candidate
                    parent[nxt][k] = j
    cost, last = min((best[full][j] + inst.time(ids[j], DEPOT), j) for j in range(n))
    order: list[int] = []
    mask = full
    while last != -1:
        order.append(ids[last])
        last, mask = parent[mask][last], mask & ~(1 << last)
    return cost, tuple(reversed(order))
