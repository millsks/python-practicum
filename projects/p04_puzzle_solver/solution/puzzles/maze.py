"""ASCII mazes solved with A* search and a Manhattan-distance heuristic."""

import heapq
from dataclasses import dataclass

Cell = tuple[int, int]

WALL = "#"
OPEN = frozenset({".", " "})


class MazeError(ValueError):
    """Raised when maze text is malformed."""


@dataclass(frozen=True, slots=True)
class Maze:
    """A rectangular maze.

    Attributes:
        rows: The maze rows; ragged input is padded with walls.
        start: Position of ``S`` as ``(row, col)``.
        goal: Position of ``G`` as ``(row, col)``.
    """

    rows: tuple[str, ...]
    start: Cell
    goal: Cell

    @property
    def height(self) -> int:
        """Number of rows."""
        return len(self.rows)

    @property
    def width(self) -> int:
        """Number of columns."""
        return len(self.rows[0]) if self.rows else 0

    def cost(self, cell: Cell) -> int | None:
        """Return the cost of stepping onto ``cell``, or None if it is a wall or off the board.

        Open cells (``.``, space, ``S``, ``G``) cost 1 and digit cells ``1``-``9`` cost their value.

        Args:
            cell: The ``(row, col)`` position.

        Returns:
            The step cost, or None when the cell cannot be entered.
        """
        row, col = cell
        if not (0 <= row < self.height and 0 <= col < self.width):
            return None
        char = self.rows[row][col]
        if char == WALL:
            return None
        if char.isdigit():
            return int(char)
        return 1

    def neighbors(self, cell: Cell) -> list[tuple[Cell, int]]:
        """Return the enterable orthogonal neighbors of ``cell`` with their step costs.

        Args:
            cell: The current position.

        Returns:
            ``(neighbor, cost)`` pairs in up, down, left, right order.
        """
        row, col = cell
        result: list[tuple[Cell, int]] = []
        for nxt in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            step = self.cost(nxt)
            if step is not None:
                result.append((nxt, step))
        return result


def parse_maze(text: str) -> Maze:
    """Parse an ASCII maze.

    Args:
        text: Lines using ``#`` walls, ``.`` or space for open cells, digits 1-9 for weighted cells, and
            exactly one ``S`` and one ``G``.

    Returns:
        The parsed maze.

    Raises:
        MazeError: If the maze is empty, uses an unknown character, or lacks exactly one ``S`` and one ``G``.
    """
    lines = [line.rstrip("\n") for line in text.strip("\n").splitlines()]
    if not lines:
        raise MazeError("maze is empty")
    width = max(len(line) for line in lines)
    rows = tuple(line.ljust(width, WALL) for line in lines)
    found: dict[str, list[Cell]] = {"S": [], "G": []}
    for r, line in enumerate(rows):
        for c, char in enumerate(line):
            if char in found:
                found[char].append((r, c))
            elif char != WALL and char not in OPEN and not ("1" <= char <= "9"):
                raise MazeError(f"unknown character {char!r} at row {r}, column {c}")
    for marker, cells in found.items():
        if len(cells) != 1:
            raise MazeError(f"expected exactly one {marker!r}, found {len(cells)}")
    return Maze(rows, found["S"][0], found["G"][0])


def manhattan(a: Cell, b: Cell) -> int:
    """Return the Manhattan (grid) distance between two cells.

    Args:
        a: First cell.
        b: Second cell.

    Returns:
        ``|dr| + |dc|``.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def solve_maze(maze: Maze) -> tuple[list[Cell], int] | None:
    """Find a cheapest path from start to goal with A*.

    The heuristic is the Manhattan distance, which never overestimates because every step costs at least 1,
    so the first time the goal is popped its cost is optimal.

    Args:
        maze: The maze to solve.

    Returns:
        ``(path, cost)`` where ``path`` lists cells from start to goal and ``cost`` is the sum of the costs of
        every cell entered after the start, or None if the goal is unreachable.
    """
    start, goal = maze.start, maze.goal
    best: dict[Cell, int] = {start: 0}
    parent: dict[Cell, Cell] = {}
    frontier: list[tuple[int, int, Cell]] = [(manhattan(start, goal), 0, start)]
    while frontier:
        _, cost, cell = heapq.heappop(frontier)
        if cell == goal:
            path = [cell]
            while cell in parent:
                cell = parent[cell]
                path.append(cell)
            return path[::-1], cost
        if cost > best[cell]:
            continue
        for nxt, step in maze.neighbors(cell):
            new_cost = cost + step
            if new_cost < best.get(nxt, new_cost + 1):
                best[nxt] = new_cost
                parent[nxt] = cell
                heapq.heappush(frontier, (new_cost + manhattan(nxt, goal), new_cost, nxt))
    return None


def render_path(maze: Maze, path: list[Cell]) -> str:
    """Draw ``path`` onto the maze with ``*``, keeping ``S`` and ``G`` visible.

    Args:
        maze: The maze.
        path: Cells to mark.

    Returns:
        The maze text with the path drawn.
    """
    grid = [list(row) for row in maze.rows]
    for r, c in path:
        if grid[r][c] not in "SG":
            grid[r][c] = "*"
    return "\n".join("".join(row) for row in grid)
