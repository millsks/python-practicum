"""Milestones 3-5: the route model, feasibility, construction heuristics, 2-opt, and exact Held-Karp."""

import itertools
import math
import random

import pytest
from routewise.data import Customer, generate_city
from routewise.graph import DistanceMatrix, RoadGraph
from routewise.routing import (
    DEPOT,
    InfeasibleCustomerError,
    Instance,
    Plan,
    Route,
    check_plan,
    clarke_wright,
    held_karp,
    improve_plan,
    is_feasible,
    nearest_neighbor,
    plan_cost,
    route_cost,
    schedule,
    two_opt,
)


def line_instance(capacity=10.0, horizon=600.0):
    coords = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (2.0, 0.0)}
    graph = RoadGraph.from_edges(coords, [(0, 1, 10.0), (1, 2, 10.0)])
    customers = {
        1: Customer(1, 1, 3, ready=30.0, due=60.0, service=5.0),
        2: Customer(2, 2, 4, ready=0.0, due=50.0, service=5.0),
    }
    return Instance(0, customers, DistanceMatrix(graph, [0, 1, 2]), capacity, horizon, coords)


def tiny_tsp(seed, n):
    rng = random.Random(seed)
    coords = {i: (rng.uniform(0, 10), rng.uniform(0, 10)) for i in range(n + 1)}
    edges = [(a, b, math.dist(coords[a], coords[b])) for a, b in itertools.combinations(coords, 2)]
    graph = RoadGraph.from_edges(coords, edges)
    customers = {i: Customer(i, i, 1, 0.0, math.inf, 0.0) for i in range(1, n + 1)}
    return Instance(0, customers, DistanceMatrix(graph, list(coords)), math.inf, math.inf, coords)


def brute_force(inst):
    ids = sorted(inst.customers)
    return min(route_cost(p, inst) for p in itertools.permutations(ids))


@pytest.fixture(scope="module")
def city_instance():
    return Instance.from_city(generate_city(45, seed=21), capacity=40)


def test_route_and_plan_are_immutable_tuples():
    route = Route([3, 1, 2])
    assert route.stops == (3, 1, 2) and len(route) == 3, "stops should be stored as a tuple"
    plan = Plan([route, Route([4])], "manual")
    assert plan.customers() == [3, 1, 2, 4]
    with pytest.raises(AttributeError):
        route.stops = (1,)


def test_schedule_waits_for_window_to_open():
    inst = line_instance()
    s = schedule(Route((1, 2)), inst)
    assert [v.arrival for v in s.visits] == [10.0, 45.0], "arrivals: drive 10, wait until 30, serve 5, drive 10"
    assert s.visits[0].start == 30.0 and s.visits[0].wait == 20.0, "the van must wait for customer 1 to open"
    assert s.travel_minutes == 40.0 and s.end_time == 70.0 and s.load == 7
    assert s.feasible and s.total_wait == 20.0


def test_schedule_detects_capacity_and_horizon():
    s = schedule((1, 2), line_instance(capacity=6, horizon=60))
    assert any("capacity" in v for v in s.violations), "load 7 exceeds capacity 6"
    assert any("horizon" in v for v in s.violations), "back at 70 is after horizon 60"
    assert not s.feasible


def test_schedule_detects_late_arrival():
    inst = line_instance()
    late = Instance(
        inst.depot, {**inst.customers, 2: Customer(2, 2, 4, 0.0, 40.0, 5.0)}, inst.travel, 10, 600, inst.coords
    )
    s = schedule((1, 2), late)
    assert any("late at customer 2" in v for v in s.violations), "arriving at 45 misses a window closing at 40"
    assert schedule((2, 1), late).feasible, "the reverse order serves both in time"


def test_route_cost_includes_depot_legs():
    inst = line_instance()
    assert route_cost((), inst) == 0.0
    assert route_cost((2,), inst) == 40.0 and route_cost((1, 2), inst) == 40.0
    assert inst.time(DEPOT, 2) == 20.0


def test_check_plan_reports_missing_duplicate_and_unknown():
    inst = line_instance()
    problems = check_plan(Plan((Route((1, 1)), Route((9,)))), inst)
    text = " ".join(problems)
    assert "visited twice" in text and "unknown customer 9" in text and "customer 2 is not served" in text
    assert is_feasible(Plan((Route((2, 1)),)), inst)


@pytest.mark.parametrize("seed", range(6))
def test_held_karp_matches_brute_force(seed):
    inst = tiny_tsp(seed, 6)
    cost, order = held_karp(inst)
    assert math.isclose(cost, brute_force(inst)), "Held-Karp must find the optimal tour"
    assert sorted(order) == sorted(inst.customers), "the tour must visit every customer exactly once"
    assert math.isclose(route_cost(order, inst), cost), "the returned order must achieve the returned cost"


def test_held_karp_edge_cases():
    assert held_karp(tiny_tsp(0, 3), customers=[]) == (0.0, ())
    with pytest.raises(ValueError):
        held_karp(tiny_tsp(0, 13))


@pytest.mark.parametrize("seed", range(8))
def test_heuristics_are_never_better_than_optimal_and_close_to_it(seed):
    inst = tiny_tsp(seed, 9)
    optimum, _ = held_karp(inst)
    for build in (nearest_neighbor, clarke_wright):
        plan = build(inst)
        assert len(plan.routes) == 1, "with no limits everything fits on one route"
        polished = two_opt(plan.routes[0], inst)
        assert route_cost(polished, inst) >= optimum - 1e-9, "no heuristic can beat the exact optimum"
        assert route_cost(polished, inst) <= 1.15 * optimum, "heuristic + 2-opt should be within 15% here"


@pytest.mark.parametrize("seed", range(10))
def test_property_two_opt_never_worsens_and_keeps_stops(seed):
    inst = tiny_tsp(seed, 10)
    stops = list(inst.customers)
    random.Random(seed).shuffle(stops)
    better = two_opt(Route(tuple(stops)), inst)
    assert route_cost(better, inst) <= route_cost(stops, inst) + 1e-9, "2-opt must never lengthen a route"
    assert sorted(better.stops) == sorted(stops), "2-opt must keep exactly the same customers"


def test_two_opt_untangles_a_crossing():
    coords = {0: (0.0, 0.0), 1: (0.0, 1.0), 2: (1.0, 1.0), 3: (1.0, 0.0)}
    edges = [(a, b, math.dist(coords[a], coords[b])) for a, b in itertools.combinations(coords, 2)]
    graph = RoadGraph.from_edges(coords, edges)
    customers = {i: Customer(i, i, 1, 0.0, math.inf, 0.0) for i in (1, 2, 3)}
    inst = Instance(0, customers, DistanceMatrix(graph, [0, 1, 2, 3]), math.inf, math.inf, coords)
    crossed = Route((2, 1, 3))
    assert route_cost(two_opt(crossed, inst), inst) == pytest.approx(4.0), "the square's perimeter is optimal"


@pytest.mark.parametrize("build", [nearest_neighbor, clarke_wright])
def test_constructed_plans_are_feasible(build, city_instance):
    plan = build(city_instance)
    assert check_plan(plan, city_instance) == [], "every produced plan must be feasible and complete"
    improved = improve_plan(plan, city_instance)
    assert check_plan(improved, city_instance) == [], "2-opt must preserve feasibility"
    assert plan_cost(improved, city_instance) <= plan_cost(plan, city_instance) + 1e-9, "2-opt never worsens"


def test_savings_beats_nearest_neighbor_on_generated_cities():
    total_nn = total_cw = 0.0
    for seed in range(3):
        inst = Instance.from_city(generate_city(40, seed=seed), capacity=50)
        total_nn += plan_cost(nearest_neighbor(inst), inst)
        total_cw += plan_cost(clarke_wright(inst), inst)
    assert total_cw < total_nn, "Clarke-Wright should usually produce shorter plans than nearest neighbour"


def test_unservable_customer_raises():
    inst = line_instance()
    impossible = Instance(
        inst.depot, {**inst.customers, 2: Customer(2, 2, 4, 0.0, 5.0, 5.0)}, inst.travel, 10, 600, inst.coords
    )
    with pytest.raises(InfeasibleCustomerError):
        nearest_neighbor(impossible)
    with pytest.raises(InfeasibleCustomerError):
        clarke_wright(impossible)


def test_instance_subset_and_relaxed(city_instance):
    sub = city_instance.subset([1, 2, 3])
    assert sorted(sub.customers) == [1, 2, 3]
    relaxed = city_instance.relaxed()
    assert relaxed.capacity == math.inf and all(c.due == math.inf for c in relaxed.customers.values())
    assert len(nearest_neighbor(relaxed).routes) == 1, "a relaxed instance needs a single route"
