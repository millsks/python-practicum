"""City data model, a deterministic synthetic city generator, and CSV persistence."""

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path

from routewise.graph import RoadGraph, dijkstra

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
        if self.id < 1:
            raise ValueError(f"customer id must be >= 1, got {self.id}")
        if self.demand < 0 or self.service < 0:
            raise ValueError("demand and service time must be non-negative")
        if self.ready > self.due:
            raise ValueError(f"customer {self.id}: ready {self.ready} is after due {self.due}")


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
        return RoadGraph.from_edges(self.coords(), ((e.u, e.v, e.minutes) for e in self.edges))

    def coords(self) -> dict[int, tuple[float, float]]:
        """Return a mapping from node id to ``(x, y)``."""
        return {n.id: (n.x, n.y) for n in self.nodes}

    def customer(self, customer_id: int) -> Customer:
        """Look up a customer by id.

        Raises:
            KeyError: If there is no such customer.
        """
        for customer in self.customers:
            if customer.id == customer_id:
                return customer
        raise KeyError(f"unknown customer {customer_id}")


def _ceil3(value: float) -> float:
    return math.ceil(value * 1000) / 1000


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
    if n_customers < 1:
        raise ValueError("a city needs at least one customer")
    rng = random.Random(seed)
    side = max(3, math.ceil(math.sqrt(n_customers * 1.6 + 1)))
    nodes = tuple(
        Node(
            r * side + c,
            round(c * GRID_SPACING + rng.uniform(-0.12, 0.12), 3),
            round(r * GRID_SPACING + rng.uniform(-0.12, 0.12), 3),
        )
        for r in range(side)
        for c in range(side)
    )

    def segment(a: int, b: int) -> Edge:
        length = math.hypot(nodes[a].x - nodes[b].x, nodes[a].y - nodes[b].y)
        return Edge(a, b, _ceil3(length / MAX_SPEED * rng.uniform(1.0, 1.7)))

    edges: list[Edge] = []
    for r in range(side):
        for c in range(side):
            here = r * side + c
            if c + 1 < side:
                edges.append(segment(here, here + 1))
            if r + 1 < side:
                edges.append(segment(here, here + side))
            if r + 1 < side and c + 1 < side and rng.random() < 0.2:
                edges.append(segment(here, here + side + 1))
    depot = (side // 2) * side + side // 2
    graph = RoadGraph.from_edges({n.id: (n.x, n.y) for n in nodes}, ((e.u, e.v, e.minutes) for e in edges))
    from_depot, _ = dijkstra(graph, depot)
    candidates = [n.id for n in nodes if n.id != depot]
    customers: list[Customer] = []
    for customer_id, node in enumerate(rng.sample(candidates, n_customers), start=1):
        ready = float(rng.randrange(0, 361, 5))
        width = float(rng.choice((60, 90, 120, 180)))
        due = max(ready + width, math.ceil(from_depot[node]) + width)
        customers.append(Customer(customer_id, node, rng.randint(1, 8), ready, due, round(rng.uniform(2.0, 8.0), 1)))
    return City(nodes, tuple(edges), tuple(customers), depot)


def save_city(city: City, directory: Path) -> list[Path]:
    """Write a city as three CSV files (nodes, edges, customers).

    Args:
        city: City to save.
        directory: Destination directory; created if missing.

    Returns:
        The written file paths.
    """
    directory.mkdir(parents=True, exist_ok=True)
    tables: dict[str, tuple[list[str], list[list[object]]]] = {
        NODES_FILE: (["id", "x", "y", "is_depot"], [[n.id, n.x, n.y, int(n.id == city.depot)] for n in city.nodes]),
        EDGES_FILE: (["u", "v", "minutes"], [[e.u, e.v, e.minutes] for e in city.edges]),
        CUSTOMERS_FILE: (
            ["id", "node", "demand", "ready", "due", "service"],
            [[c.id, c.node, c.demand, c.ready, c.due, c.service] for c in city.customers],
        ),
    }
    written: list[Path] = []
    for name, (header, rows) in tables.items():
        path = directory / name
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)
        written.append(path)
    return written


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
    node_rows = _read(directory / NODES_FILE)
    nodes = tuple(Node(int(r["id"]), float(r["x"]), float(r["y"])) for r in node_rows)
    depots = [int(r["id"]) for r in node_rows if r["is_depot"] == "1"]
    if len(depots) != 1:
        raise ValueError(f"{NODES_FILE} must mark exactly one depot, found {len(depots)}")
    edges = tuple(Edge(int(r["u"]), int(r["v"]), float(r["minutes"])) for r in _read(directory / EDGES_FILE))
    customers = tuple(
        Customer(
            int(r["id"]), int(r["node"]), int(r["demand"]), float(r["ready"]), float(r["due"]), float(r["service"])
        )
        for r in _read(directory / CUSTOMERS_FILE)
    )
    return City(nodes, edges, tuple(sorted(customers, key=lambda c: c.id)), depots[0])
