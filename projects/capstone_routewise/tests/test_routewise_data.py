"""Milestone 1: the city data model, the deterministic generator, and CSV round trips."""

import math

import pytest
from routewise.data import MAX_SPEED, Customer, generate_city, load_city, save_city
from routewise.graph import dijkstra


def test_same_seed_gives_identical_city():
    assert generate_city(25, seed=3) == generate_city(25, seed=3), "the generator must be deterministic per seed"


def test_different_seeds_give_different_cities():
    assert generate_city(25, seed=1) != generate_city(25, seed=2), "different seeds should produce different cities"


@pytest.mark.parametrize("n", [1, 30, 120])
def test_customer_ids_and_nodes(n):
    city = generate_city(n, seed=0)
    assert [c.id for c in city.customers] == list(range(1, n + 1)), "customer ids must be 1..n in order"
    nodes = [c.node for c in city.customers]
    assert len(set(nodes)) == n, "each customer needs its own intersection"
    assert city.depot not in nodes, "no customer may sit on the depot"
    known = {node.id for node in city.nodes}
    assert set(nodes) <= known, "customers must sit on existing nodes"


def test_customer_fields_are_sensible():
    for c in generate_city(80, seed=5).customers:
        assert 1 <= c.demand <= 8, f"demand of customer {c.id} out of range"
        assert c.ready < c.due, f"customer {c.id} has an empty window"
        assert c.service > 0, f"customer {c.id} needs a positive service time"


def test_network_is_connected_and_every_customer_reachable_in_time():
    city = generate_city(60, seed=7)
    dist, _ = dijkstra(city.road_graph(), city.depot)
    assert len(dist) == len(city.nodes), "every intersection must be reachable from the depot"
    for c in city.customers:
        assert dist[c.node] <= c.due, f"a van leaving at 0 must be able to reach customer {c.id} before it closes"


def test_edge_times_respect_max_speed():
    city = generate_city(40, seed=2)
    coords = city.coords()
    for e in city.edges:
        (ax, ay), (bx, by) = coords[e.u], coords[e.v]
        assert e.minutes >= math.hypot(ax - bx, ay - by) / MAX_SPEED - 1e-9, "no road may be faster than MAX_SPEED"


def test_csv_round_trip(tmp_path):
    city = generate_city(30, seed=11)
    written = save_city(city, tmp_path / "city")
    assert {p.name for p in written} == {"nodes.csv", "edges.csv", "customers.csv"}, "three CSV files expected"
    assert load_city(tmp_path / "city") == city, "loading a saved city must give back an equal city"


def test_load_missing_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_city(tmp_path / "nope")


def test_generate_rejects_zero_customers():
    with pytest.raises(ValueError):
        generate_city(0)


def test_customer_validation():
    with pytest.raises(ValueError):
        Customer(1, 5, 3, ready=100.0, due=50.0, service=5.0)
    with pytest.raises(ValueError):
        Customer(0, 5, 3, ready=0.0, due=50.0, service=5.0)
