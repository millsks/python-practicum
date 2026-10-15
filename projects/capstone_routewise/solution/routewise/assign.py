"""Splitting customers across vans: the sweep algorithm and a single entry point for every planner."""

import math
from collections.abc import Callable

from routewise.routing import Instance, Plan, Route, clarke_wright, improve_plan, nearest_neighbor

METHODS = ("nearest", "savings", "sweep")
"""Planning methods accepted by :func:`plan_routes`."""


def polar_angle(inst: Instance, customer_id: int) -> float:
    """Angle in radians, in ``[0, 2*pi)``, of a customer as seen from the depot (east is 0, counter-clockwise).

    Raises:
        KeyError: If coordinates for the depot or the customer are missing.
    """
    dx, dy = inst.coords[inst.node(customer_id)]
    ox, oy = inst.coords[inst.depot]
    return math.atan2(dy - oy, dx - ox) % (2 * math.pi)


def sweep_clusters(inst: Instance, start_angle: float = 0.0) -> list[list[int]]:
    """Group customers by sweeping a ray around the depot, starting a new group when a van would overflow.

    Args:
        inst: Problem instance with coordinates.
        start_angle: Angle in radians at which the sweep begins.

    Returns:
        Groups of customer ids, each with total demand at most the van capacity, in sweep order.
    """
    order = sorted(inst.customers, key=lambda cid: ((polar_angle(inst, cid) - start_angle) % (2 * math.pi), cid))
    clusters: list[list[int]] = []
    load = math.inf
    for cid in order:
        demand = inst.customers[cid].demand
        if load + demand > inst.capacity:
            clusters.append([])
            load = 0.0
        clusters[-1].append(cid)
        load += demand
    return clusters


def sweep(inst: Instance, start_angle: float = 0.0) -> Plan:
    """Cluster-first, route-second: sweep into capacity-feasible groups, then route each group greedily.

    A group whose time windows do not fit on one route is split further by :func:`nearest_neighbor`.

    Args:
        inst: Problem instance with coordinates.
        start_angle: Angle in radians at which the sweep begins.

    Returns:
        A feasible plan.
    """
    routes: list[Route] = []
    for cluster in sweep_clusters(inst, start_angle):
        routes.extend(nearest_neighbor(inst, cluster).routes)
    return Plan(tuple(routes), "sweep")


def plan_routes(inst: Instance, method: str = "savings", *, improve: bool = True) -> Plan:
    """Plan a day's routes with the chosen construction method, optionally polished by 2-opt.

    Args:
        inst: Problem instance.
        method: One of :data:`METHODS`.
        improve: Apply 2-opt to every route afterwards.

    Returns:
        A feasible plan.

    Raises:
        ValueError: If ``method`` is unknown.
    """
    builders: dict[str, Callable[[Instance], Plan]] = {
        "nearest": nearest_neighbor,
        "savings": clarke_wright,
        "sweep": sweep,
    }
    if method not in builders:
        raise ValueError(f"unknown method {method!r}; choose from {', '.join(METHODS)}")
    plan = builders[method](inst)
    return improve_plan(plan, inst) if improve else plan


def vans_short(plan: Plan, n_vans: int) -> int:
    """How many more vans the plan needs than the fleet has (0 when the fleet suffices)."""
    return max(0, len(plan.routes) - n_vans)
