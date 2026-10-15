"""Road network graph, shortest paths (Dijkstra and A*), and a cached travel-time matrix."""

import heapq  # noqa: F401
import math  # noqa: F401
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
        # TODO: store coordinates in one dict and an adjacency list (node -> list of (neighbor, minutes)).
        raise NotImplementedError

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
        # TODO: create an empty graph, add every node, then every edge.
        raise NotImplementedError

    def add_node(self, node: int, x: float, y: float) -> None:
        """Add an intersection, or move an existing one.

        Args:
            node: Node id.
            x: Easting in kilometres.
            y: Northing in kilometres.
        """
        # TODO: implement this function.
        raise NotImplementedError

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
        # TODO: validate both nodes exist (KeyError) and minutes is finite and >= 0 (ValueError).
        raise NotImplementedError

    def neighbors(self, node: int) -> tuple[tuple[int, float], ...]:
        """Return the ``(neighbor, minutes)`` arcs leaving ``node``.

        Raises:
            KeyError: If the node is unknown.
        """
        # TODO: implement this function.
        raise NotImplementedError

    def coords(self, node: int) -> tuple[float, float]:
        """Return the ``(x, y)`` coordinates of ``node``."""
        # TODO: implement this function.
        raise NotImplementedError

    @property
    def nodes(self) -> list[int]:
        """All node ids in ascending order."""
        # TODO: implement this function.
        raise NotImplementedError

    @property
    def arc_count(self) -> int:
        """Number of directed arcs (a two-way street counts twice)."""
        # TODO: implement this function.
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of nodes."""
        return len(self._adj)

    def __contains__(self, node: object) -> bool:
        """Return whether ``node`` is in the graph."""
        return node in self._adj

    def euclidean(self, a: int, b: int) -> float:
        """Straight-line distance in kilometres between two nodes."""
        # TODO: implement this function.
        raise NotImplementedError

    def max_speed(self) -> float:
        """Return the fastest speed (km per minute) of any arc.

        Dividing straight-line distance by this speed never overestimates the true travel time, which makes it an
        admissible A* heuristic for this graph. Returns ``math.inf`` if some arc covers distance in zero minutes.
        """
        # TODO: max over arcs of euclidean length / minutes; a zero-minute arc of positive length means inf.
        raise NotImplementedError


def reconstruct_path(prev: Mapping[int, int], source: int, target: int) -> tuple[int, ...]:
    """Walk predecessor links back from ``target`` to ``source``.

    Args:
        prev: Predecessor of each settled node (the source has none).
        source: Start node.
        target: End node.

    Returns:
        The path ``source .. target``, or an empty tuple if ``target`` was never reached.
    """
    # TODO: follow prev[] from target back to source, then reverse; return () if target unreached.
    raise NotImplementedError


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
    # TODO: heapq of (distance, node); skip stale entries; relax arcs; stop early when target is popped.
    raise NotImplementedError


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
    # TODO: implement this function.
    raise NotImplementedError


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
    # TODO: like Dijkstra but order the heap by g + h where h = euclidean(n, target) / max_speed.
    raise NotImplementedError


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
        # TODO: implement this function.
        raise NotImplementedError

    def _row(self, source: int) -> dict[int, float]:
        # TODO: run dijkstra from source once, cache the distances, and count the run.
        raise NotImplementedError

    def cost(self, a: int, b: int) -> float:
        """Shortest travel minutes from node ``a`` to node ``b`` (``math.inf`` if unreachable)."""
        # TODO: 0 for a == b, otherwise look up the cached row of a (inf if unreachable).
        raise NotImplementedError

    def as_array(self) -> np.ndarray:
        """Return the full matrix as a float array indexed in ``nodes`` order."""
        # TODO: implement this function.
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of indexed nodes."""
        return len(self.nodes)
