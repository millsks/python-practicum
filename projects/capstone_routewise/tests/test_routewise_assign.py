"""Milestone 5: splitting customers across vans with the sweep algorithm and the planning entry point."""

import math

import pytest
from routewise.assign import METHODS, plan_routes, polar_angle, sweep, sweep_clusters, vans_short
from routewise.data import Customer, generate_city
from routewise.graph import DistanceMatrix, RoadGraph
from routewise.routing import Instance, check_plan, plan_cost


@pytest.fixture(scope="module")
def inst():
    return Instance.from_city(generate_city(50, seed=8), capacity=35)


def test_polar_angle_compass_points():
    coords = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (0.0, 1.0), 3: (-1.0, 0.0), 4: (0.0, -1.0)}
    graph = RoadGraph.from_edges(coords, [(0, i, 1.0) for i in range(1, 5)])
    customers = {i: Customer(i, i, 1, 0.0, 100.0, 1.0) for i in range(1, 5)}
    compass = Instance(0, customers, DistanceMatrix(graph, list(coords)), 10, 600, coords)
    expected = [0.0, math.pi / 2, math.pi, 3 * math.pi / 2]
    for cid, angle in zip(range(1, 5), expected, strict=True):
        assert polar_angle(compass, cid) == pytest.approx(angle), f"customer {cid} should be at {angle:.2f} rad"
    assert [len(c) for c in sweep_clusters(compass.subset([1, 2, 3, 4]))] == [4], "all four fit one van"


def test_sweep_clusters_partition_and_respect_capacity(inst):
    clusters = sweep_clusters(inst)
    flat = [cid for cluster in clusters for cid in cluster]
    assert sorted(flat) == sorted(inst.customers), "clusters must partition the customers"
    for cluster in clusters:
        assert sum(inst.customers[c].demand for c in cluster) <= inst.capacity, "a cluster may not overflow a van"
    angles = [polar_angle(inst, cid) for cid in flat]
    assert angles == sorted(angles), "customers appear in sweep (angle) order"


def test_sweep_plan_is_feasible(inst):
    plan = sweep(inst)
    assert plan.method == "sweep"
    assert check_plan(plan, inst) == [], "the sweep plan must be feasible and complete"


@pytest.mark.parametrize("method", METHODS)
def test_every_method_gives_feasible_plan(inst, method):
    plan = plan_routes(inst, method)
    assert check_plan(plan, inst) == [], f"{method} must give a feasible plan"
    raw = plan_routes(inst, method, improve=False)
    assert plan_cost(plan, inst) <= plan_cost(raw, inst) + 1e-9, "improvement must never make a plan longer"


def test_unknown_method_rejected(inst):
    with pytest.raises(ValueError):
        plan_routes(inst, "teleport")


def test_vans_short():
    plan = plan_routes(Instance.from_city(generate_city(30, seed=1), capacity=20), "savings")
    assert vans_short(plan, 100) == 0
    assert vans_short(plan, 1) == len(plan.routes) - 1


@pytest.mark.parametrize("n", [30, 200])
def test_scales_to_target_sizes(n):
    inst = Instance.from_city(generate_city(n, seed=n), capacity=60)
    plan = plan_routes(inst, "savings")
    assert check_plan(plan, inst) == [], f"a {n}-customer day must be planned feasibly"
