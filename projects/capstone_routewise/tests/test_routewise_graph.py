"""Milestone 2: the road graph, Dijkstra, A*, and the cached distance matrix."""

import itertools
import math
import random

import pytest
from routewise.data import generate_city
from routewise.graph import DistanceMatrix, RoadGraph, a_star, dijkstra, reconstruct_path, shortest_path


@pytest.fixture
def diamond():
    #   0 --1-- 1 --1-- 3     plus a slow direct road 0-3 (10) and 0-2-3 (2 + 2)
    coords = {0: (0.0, 0.0), 1: (1.0, 1.0), 2: (1.0, -1.0), 3: (2.0, 0.0), 4: (9.0, 9.0)}
    edges = [(0, 1, 1.5), (1, 3, 1.5), (0, 2, 2.0), (2, 3, 2.0), (0, 3, 10.0)]
    return RoadGraph.from_edges(coords, edges)


def random_graph(seed, n=25):
    rng = random.Random(seed)
    coords = {i: (rng.uniform(0, 10), rng.uniform(0, 10)) for i in range(n)}
    graph = RoadGraph()
    for node, (x, y) in coords.items():
        graph.add_node(node, x, y)
    for i in range(1, n):
        j = rng.randrange(i)
        graph.add_edge(i, j, math.dist(coords[i], coords[j]) * rng.uniform(1.0, 2.0))
    for _ in range(n):
        i, j = rng.sample(range(n), 2)
        graph.add_edge(i, j, math.dist(coords[i], coords[j]) * rng.uniform(1.0, 2.0), both_ways=rng.random() < 0.5)
    return graph


def test_graph_basics(diamond):
    assert len(diamond) == 5, "five nodes"
    assert diamond.arc_count == 10, "five two-way edges are ten arcs"
    assert 4 in diamond and 99 not in diamond
    assert sorted(diamond.neighbors(0)) == [(1, 1.5), (2, 2.0), (3, 10.0)]


def test_dijkstra_distances(diamond):
    dist, prev = dijkstra(diamond, 0)
    assert dist == {0: 0.0, 1: 1.5, 2: 2.0, 3: 3.0}, "node 4 is isolated so it must be absent"
    assert reconstruct_path(prev, 0, 3) == (0, 1, 3)


def test_shortest_path_and_unreachable(diamond):
    result = shortest_path(diamond, 0, 3)
    assert result.cost == 3.0 and result.path == (0, 1, 3)
    missing = shortest_path(diamond, 0, 4)
    assert missing.cost == math.inf and missing.path == () and not missing.found


def test_a_star_matches_dijkstra_on_small_graph(diamond):
    result = a_star(diamond, 0, 3)
    assert result.cost == pytest.approx(3.0) and result.path == (0, 1, 3)
    assert a_star(diamond, 0, 4).path == (), "unreachable target gives an empty path"


def test_bad_edges_rejected(diamond):
    with pytest.raises(ValueError):
        diamond.add_edge(0, 1, -1.0)
    with pytest.raises(KeyError):
        diamond.add_edge(0, 42, 1.0)
    with pytest.raises(KeyError):
        shortest_path(diamond, 0, 42)


def path_cost(graph, path):
    total = 0.0
    for u, v in itertools.pairwise(path):
        total += min(w for n, w in graph.neighbors(u) if n == v)
    return total


@pytest.mark.parametrize("seed", range(12))
def test_property_a_star_equals_dijkstra_on_random_graphs(seed):
    graph = random_graph(seed)
    rng = random.Random(seed + 100)
    for _ in range(10):
        s, t = rng.sample(graph.nodes, 2)
        d, a = shortest_path(graph, s, t), a_star(graph, s, t)
        assert math.isclose(d.cost, a.cost) or d.cost == a.cost == math.inf, f"A* and Dijkstra disagree {s}->{t}"
        if a.found:
            assert a.path[0] == s and a.path[-1] == t, "path must start at the source and end at the target"
            assert math.isclose(path_cost(graph, a.path), a.cost), "reported cost must equal the path's arc sum"


def test_heuristic_is_admissible_and_a_star_explores_less():
    city = generate_city(60, seed=4)
    graph = city.road_graph()
    speed = graph.max_speed()
    nodes = graph.nodes
    expanded_a = expanded_d = 0
    for t in nodes[::7]:
        dist, _ = dijkstra(graph, t)
        for n in nodes[::5]:
            assert graph.euclidean(n, t) / speed <= dist[n] + 1e-9, "straight line / max speed must not overestimate"
        a, d = a_star(graph, city.depot, t), shortest_path(graph, city.depot, t)
        expanded_a += a.expanded
        expanded_d += d.expanded
    assert expanded_a < expanded_d, "A* should settle fewer nodes than Dijkstra overall"


def test_distance_matrix_values_and_caching():
    city = generate_city(20, seed=9)
    graph = city.road_graph()
    nodes = [city.depot, *(c.node for c in city.customers)]
    matrix = DistanceMatrix(graph, nodes)
    assert matrix.dijkstra_runs == 0, "rows are computed lazily"
    for a in nodes[:5]:
        for b in nodes[:5]:
            assert math.isclose(matrix.cost(a, b), shortest_path(graph, a, b).cost), "matrix must hold shortest times"
    runs = matrix.dijkstra_runs
    assert runs <= 5, "one Dijkstra per source row at most"
    matrix.cost(nodes[0], nodes[3])
    assert matrix.dijkstra_runs == runs, "a cached row must not be recomputed"
    array = matrix.as_array()
    assert array.shape == (21, 21) and (array.diagonal() == 0).all()
    assert abs(array - array.T).max() < 1e-9, "two-way roads give a symmetric matrix"


def test_distance_matrix_rejects_duplicates():
    graph = RoadGraph.from_edges({0: (0, 0), 1: (1, 0)}, [(0, 1, 1.0)])
    with pytest.raises(ValueError):
        DistanceMatrix(graph, [0, 0])
