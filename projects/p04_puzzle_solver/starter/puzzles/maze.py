"""ASCII mazes solved with A* search and a Manhattan-distance heuristic."""

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
        # TODO: None for walls and positions off the board; digits cost their value; everything else costs 1.
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> list[tuple[Cell, int]]:
        """Return the enterable orthogonal neighbors of ``cell`` with their step costs.

        Args:
            cell: The current position.

        Returns:
            ``(neighbor, cost)`` pairs in up, down, left, right order.
        """
        # TODO: Check up, down, left, right (in that order) and keep the ones whose cost() is not None.
        raise NotImplementedError


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
    # TODO: Strip blank leading/trailing lines, pad short rows with '#', validate characters,
    # TODO: and find exactly one 'S' and one 'G' (raise MazeError otherwise).
    raise NotImplementedError


def manhattan(a: Cell, b: Cell) -> int:
    """Return the Manhattan (grid) distance between two cells.

    Args:
        a: First cell.
        b: Second cell.

    Returns:
        ``|dr| + |dc|``.
    """
    # TODO: abs(row difference) + abs(column difference).
    raise NotImplementedError


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
    # TODO: A*: a heapq of (cost + manhattan(cell, goal), cost, cell), a best-cost dict, and parents.
    # TODO: Skip stale heap entries; when the goal is popped, rebuild the path from parents.
    raise NotImplementedError


def render_path(maze: Maze, path: list[Cell]) -> str:
    """Draw ``path`` onto the maze with ``*``, keeping ``S`` and ``G`` visible.

    Args:
        maze: The maze.
        path: Cells to mark.

    Returns:
        The maze text with the path drawn.
    """
    # TODO: Copy the rows into lists, put '*' on path cells that are not S or G, and join.
    raise NotImplementedError
