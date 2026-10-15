"""City data model, a deterministic synthetic city generator, and CSV persistence."""

import csv  # noqa: F401
import math  # noqa: F401
import random  # noqa: F401
from dataclasses import dataclass
from pathlib import Path

from routewise.graph import RoadGraph, dijkstra  # noqa: F401

MAX_SPEED = 0.8
"""Fastest van speed on any road, in kilometres per minute (48 km/h)."""

DEFAULT_HORIZON = 600.0
"""Length of the working day in minutes; every van must be back at the depot by then."""

GRID_SPACING = 0.5
"""Distance in kilometres between neighbouring intersections before jitter."""

NODES_FILE = "nodes.csv"
EDGES_FILE = "edges.csv"
CUSTOMERS_FILE = "customers.csv"


@dataclass(frozen=True, slots=True)
class Node:
    """A road intersection.

    Attributes:
        id: Node id.
        x: Easting in kilometres.
        y: Northing in kilometres.
    """

    id: int
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Edge:
    """A two-way road segment.

    Attributes:
        u: One end node.
        v: Other end node.
        minutes: Travel time in minutes.
    """

    u: int
    v: int
    minutes: float


@dataclass(frozen=True, slots=True)
class Customer:
    """A delivery stop with demand, a time window, and a service time.

    Times are minutes after the start of the working day.

    Attributes:
        id: Customer id (1 or more; 0 is reserved for the depot).
        node: Road node where the customer is located.
        demand: Number of crates to deliver.
        ready: Earliest service start.
        due: Latest service start.
        service: Minutes spent unloading.
    """

    id: int
    node: int
    demand: int
    ready: float
    due: float
    service: float

    def __post_init__(self) -> None:
        """Validate the record.

        Raises:
            ValueError: If the id is not positive, demand or service is negative, or the window is inverted.
        """
        # TODO: raise ValueError for id < 1, negative demand/service, or ready > due.
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class City:
    """A road network with a depot and customers.

    Attributes:
        nodes: Intersections.
        edges: Two-way road segments.
        customers: Customers sorted by id.
        depot: Node id of the bakery depot.
    """

    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    customers: tuple[Customer, ...]
    depot: int

    def road_graph(self) -> RoadGraph:
        """Build the :class:`RoadGraph` for this city."""
        # TODO: implement this function.
        raise NotImplementedError

    def coords(self) -> dict[int, tuple[float, float]]:
        """Return a mapping from node id to ``(x, y)``."""
        # TODO: implement this function.
        raise NotImplementedError

    def customer(self, customer_id: int) -> Customer:
        """Look up a customer by id.

        Raises:
            KeyError: If there is no such customer.
        """
        # TODO: implement this function.
        raise NotImplementedError


def _ceil3(value: float) -> float:
    # TODO: implement this function.
    raise NotImplementedError


def generate_city(n_customers: int, seed: int = 0) -> City:
    """Generate a reproducible synthetic city.

    The road network is a jittered square grid with some diagonal shortcuts. Each arc's travel time is its length
    divided by :data:`MAX_SPEED`, multiplied by a congestion factor of at least 1, so straight-line distance over
    ``MAX_SPEED`` is an admissible A* heuristic. The depot sits at the centre; customers occupy distinct other nodes
    and every customer can be served by a van that drives straight to it.

    Args:
        n_customers: Number of customers (at least 1).
        seed: Random seed; the same seed always produces the same city.

    Returns:
        The generated city.

    Raises:
        ValueError: If ``n_customers`` is less than 1.
    """
    # TODO: use random.Random(seed) only; jittered grid, diagonals, congestion factor >= 1, depot at centre.
    raise NotImplementedError


def save_city(city: City, directory: Path) -> list[Path]:
    """Write a city as three CSV files (nodes, edges, customers).

    Args:
        city: City to save.
        directory: Destination directory; created if missing.

    Returns:
        The written file paths.
    """
    # TODO: csv.writer, one file per table; mark the depot with an is_depot column.
    raise NotImplementedError


def _read(path: Path) -> list[dict[str, str]]:
    # TODO: implement this function.
    raise NotImplementedError


def load_city(directory: Path) -> City:
    """Load a city written by :func:`save_city`.

    Args:
        directory: Directory containing the three CSV files.

    Returns:
        The city.

    Raises:
        FileNotFoundError: If a file is missing.
        ValueError: If the files are malformed or name no depot.
    """
    # TODO: csv.DictReader; convert types; exactly one depot; sort customers by id.
    raise NotImplementedError
