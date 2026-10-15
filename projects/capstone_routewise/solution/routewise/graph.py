"""Road network graph, shortest paths (Dijkstra and A*), and a cached travel-time matrix."""

import heapq
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Self

import numpy as np


@dataclass(frozen=True, slots=True)
class PathResult:
    """The outcome of a single-pair shortest-path query.

    Attributes:
        cost: Total travel minutes along the path, or ``math.inf`` when the target is unreachable.
        path: Node ids from source to target inclusive; empty when unreachable.
        expanded: How many nodes were popped from the priority queue and settled.
    """

    cost: float
    path: tuple[int, ...]
    expanded: int = 0

    @property
    def found(self) -> bool:
        """Whether a path to the target exists."""
        return bool(self.path)


class RoadGraph:
    """A directed, weighted road network stored as an adjacency list.

    Nodes are intersections with planar coordinates in kilometres; arcs carry travel time in minutes.
    """

    def __init__(self) -> None:
        """Create an empty graph."""
        self._coords: dict[int, tuple[float, float]] = {}
        self._adj: dict[int, list[tuple[int, float]]] = {}

    @classmethod
    def from_edges(
        cls,
        coords: Mapping[int, tuple[float, float]],
        edges: Iterable[tuple[int, int, float]],
        *,
        both_ways: bool = True,
    ) -> Self:
        """Build a graph from node coordinates and ``(u, v, minutes)`` edges.

        Args:
            coords: Mapping from node id to ``(x, y)`` in kilometres.
            edges: Edges as ``(u, v, minutes)`` triples.
            both_ways: Add each edge in both directions (two-way streets).

        Returns:
            The populated graph.
        """
        graph = cls()
        for node, (x, y) in coords.items():
            graph.add_node(node, x, y)
        for u, v, minutes in edges:
            graph.add_edge(u, v, minutes, both_ways=both_ways)
        return graph

    def add_node(self, node: int, x: float, y: float) -> None:
        """Add an intersection, or move an existing one.

        Args:
            node: Node id.
            x: Easting in kilometres.
            y: Northing in kilometres.
        """
        self._coords[node] = (float(x), float(y))
        self._adj.setdefault(node, [])

    def add_edge(self, u: int, v: int, minutes: float, *, both_ways: bool = True) -> None:
        """Add a road segment between two existing nodes.

        Args:
            u: Start node.
            v: End node.
            minutes: Travel time; must be finite and non-negative.
            both_ways: Also add the reverse arc ``v -> u``.

        Raises:
            KeyError: If either node is unknown.
            ValueError: If ``minutes`` is negative or not finite.
        """
        for node in (u, v):
            if node not in self._adj:
                raise KeyError(f"unknown node {node}")
        if not math.isfinite(minutes) or minutes < 0:
            raise ValueError(f"travel time must be finite and non-negative, got {minutes}")
        self._adj[u].append((v, float(minutes)))
        if both_ways:
            self._adj[v].append((u, float(minutes)))

    def neighbors(self, node: int) -> tuple[tuple[int, float], ...]:
        """Return the ``(neighbor, minutes)`` arcs leaving ``node``.

        Raises:
            KeyError: If the node is unknown.
        """
        return tuple(self._adj[node])

    def coords(self, node: int) -> tuple[float, float]:
        """Return the ``(x, y)`` coordinates of ``node``."""
        return self._coords[node]

    @property
    def nodes(self) -> list[int]:
        """All node ids in ascending order."""
        return sorted(self._adj)

    @property
    def arc_count(self) -> int:
        """Number of directed arcs (a two-way street counts twice)."""
        return sum(len(arcs) for arcs in self._adj.values())

    def __len__(self) -> int:
        """Return the number of nodes."""
        return len(self._adj)

    def __contains__(self, node: object) -> bool:
        """Return whether ``node`` is in the graph."""
        return node in self._adj

    def euclidean(self, a: int, b: int) -> float:
        """Straight-line distance in kilometres between two nodes."""
        (ax, ay), (bx, by) = self._coords[a], self._coords[b]
        return math.hypot(ax - bx, ay - by)

    def max_speed(self) -> float:
        """Return the fastest speed (km per minute) of any arc.

        Dividing straight-line distance by this speed never overestimates the true travel time, which makes it an
        admissible A* heuristic for this graph. Returns ``math.inf`` if some arc covers distance in zero minutes.
        """
        fastest = 0.0
        for u, arcs in self._adj.items():
            for v, minutes in arcs:
                length = self.euclidean(u, v)
                if minutes == 0:
                    if length > 0:
                        return math.inf
                    continue
                fastest = max(fastest, length / minutes)
        return fastest


def reconstruct_path(prev: Mapping[int, int], source: int, target: int) -> tuple[int, ...]:
    """Walk predecessor links back from ``target`` to ``source``.

    Args:
        prev: Predecessor of each settled node (the source has none).
        source: Start node.
        target: End node.

    Returns:
        The path ``source .. target``, or an empty tuple if ``target`` was never reached.
    """
    if target != source and target not in prev:
        return ()
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    return tuple(reversed(path))


def dijkstra(graph: RoadGraph, source: int, target: int | None = None) -> tuple[dict[int, float], dict[int, int]]:
    """Single-source shortest travel times with a binary heap (lazy deletion).

    Args:
        graph: Road network with non-negative arc weights.
        source: Start node.
        target: Optional node at which to stop early once it is settled.

    Returns:
        ``(dist, prev)``: settled distances and predecessor links.

    Raises:
        KeyError: If ``source`` is not in the graph.
    """
    if source not in graph:
        raise KeyError(f"unknown node {source}")
    dist: dict[int, float] = {source: 0.0}
    prev: dict[int, int] = {}
    settled: set[int] = set()
    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        if u == target:
            break
        for v, w in graph.neighbors(u):
            candidate = d + w
            if candidate < dist.get(v, math.inf):
                dist[v] = candidate
                prev[v] = u
                heapq.heappush(heap, (candidate, v))
    return {n: dist[n] for n in settled}, {n: p for n, p in prev.items() if n in settled}


def shortest_path(graph: RoadGraph, source: int, target: int) -> PathResult:
    """Shortest path between two nodes using Dijkstra's algorithm with early exit.

    Args:
        graph: Road network.
        source: Start node.
        target: End node.

    Returns:
        The path, its cost, and the number of settled nodes.

    Raises:
        KeyError: If either node is unknown.
    """
    if target not in graph:
        raise KeyError(f"unknown node {target}")
    dist, prev = dijkstra(graph, source, target)
    if target not in dist:
        return PathResult(math.inf, (), len(dist))
    return PathResult(dist[target], reconstruct_path(prev, source, target), len(dist))


def a_star(graph: RoadGraph, source: int, target: int, max_speed: float | None = None) -> PathResult:
    """Shortest path guided by a straight-line-distance heuristic.

    The heuristic ``euclidean(n, target) / max_speed`` is admissible and consistent when no arc is faster than
    ``max_speed``, so the result has the same cost as Dijkstra's while usually settling fewer nodes.

    Args:
        graph: Road network.
        source: Start node.
        target: End node.
        max_speed: Upper bound on speed in km/min; defaults to ``graph.max_speed()``.

    Returns:
        The path, its cost, and the number of settled nodes.

    Raises:
        KeyError: If either node is unknown.
    """
    for node in (source, target):
        if node not in graph:
            raise KeyError(f"unknown node {node}")
    speed = graph.max_speed() if max_speed is None else max_speed

    def h(node: int) -> float:
        return 0.0 if speed in (0.0, math.inf) else graph.euclidean(node, target) / speed

    g: dict[int, float] = {source: 0.0}
    prev: dict[int, int] = {}
    closed: set[int] = set()
    heap: list[tuple[float, float, int]] = [(h(source), 0.0, source)]
    while heap:
        _, cost, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        if u == target:
            return PathResult(cost, reconstruct_path(prev, source, target), len(closed))
        for v, w in graph.neighbors(u):
            candidate = cost + w
            if candidate < g.get(v, math.inf):
                g[v] = candidate
                prev[v] = u
                heapq.heappush(heap, (candidate + h(v), candidate, v))
    return PathResult(math.inf, (), len(closed))


class DistanceMatrix:
    """Lazily computed, cached shortest travel times between a set of important nodes.

    Each row (all distances from one source) costs one full Dijkstra run and is computed at most once.
    """

    def __init__(self, graph: RoadGraph, nodes: Sequence[int]) -> None:
        """Prepare a matrix over ``nodes`` (typically the depot followed by customer nodes).

        Args:
            graph: Road network.
            nodes: Distinct node ids that index the matrix.

        Raises:
            ValueError: If ``nodes`` contains duplicates.
            KeyError: If a node is not in the graph.
        """
        if len(set(nodes)) != len(nodes):
            raise ValueError("matrix nodes must be distinct")
        for node in nodes:
            if node not in graph:
                raise KeyError(f"unknown node {node}")
        self._graph = graph
        self.nodes: tuple[int, ...] = tuple(nodes)
        self._rows: dict[int, dict[int, float]] = {}
        self.dijkstra_runs = 0

    def _row(self, source: int) -> dict[int, float]:
        row = self._rows.get(source)
        if row is None:
            row, _ = dijkstra(self._graph, source)
            self._rows[source] = row
            self.dijkstra_runs += 1
        return row

    def cost(self, a: int, b: int) -> float:
        """Shortest travel minutes from node ``a`` to node ``b`` (``math.inf`` if unreachable)."""
        if a == b:
            return 0.0
        return self._row(a).get(b, math.inf)

    def as_array(self) -> np.ndarray:
        """Return the full matrix as a float array indexed in ``nodes`` order."""
        return np.array([[self.cost(a, b) for b in self.nodes] for a in self.nodes], dtype=float)

    def __len__(self) -> int:
        """Return the number of indexed nodes."""
        return len(self.nodes)
