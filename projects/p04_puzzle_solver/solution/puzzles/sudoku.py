"""Sudoku parsing, validation, and a backtracking solver with constraint propagation."""

from collections.abc import Iterator

Grid = list[list[int]]

SIZE = 9
BOX = 3
DIGITS = frozenset(range(1, 10))


class SudokuError(ValueError):
    """Raised when text cannot be parsed into a 9x9 sudoku grid."""


def parse_grid(text: str) -> Grid:
    """Parse a sudoku from text.

    Digits 1-9 are givens; ``0`` or ``.`` mark empty cells. Whitespace and the box-drawing characters
    ``|``, ``-`` and ``+`` are ignored, so both a single 81-character line and a pretty grid parse.

    Args:
        text: The puzzle text.

    Returns:
        A 9x9 list of rows, with 0 for empty cells.

    Raises:
        SudokuError: If the text has an unexpected character or not exactly 81 cells.
    """
    cells: list[int] = []
    for char in text:
        if char.isspace() or char in "|-+":
            continue
        if char == ".":
            cells.append(0)
        elif char.isdigit():
            cells.append(int(char))
        else:
            raise SudokuError(f"unexpected character {char!r}")
    if len(cells) != SIZE * SIZE:
        raise SudokuError(f"expected 81 cells, found {len(cells)}")
    return [cells[row * SIZE : (row + 1) * SIZE] for row in range(SIZE)]


def format_grid(grid: Grid) -> str:
    """Render a grid as nine lines of digits, using ``.`` for empty cells.

    Args:
        grid: The grid to render.

    Returns:
        The text form, without a trailing newline.
    """
    return "\n".join("".join(str(v) if v else "." for v in row) for row in grid)


def _units(row: int, col: int) -> Iterator[tuple[int, int]]:
    """Yield every peer cell (same row, column, or box) of ``(row, col)``, excluding itself."""
    for i in range(SIZE):
        if i != col:
            yield row, i
        if i != row:
            yield i, col
    top, left = BOX * (row // BOX), BOX * (col // BOX)
    for r in range(top, top + BOX):
        for c in range(left, left + BOX):
            if r != row and c != col:
                yield r, c


def is_valid(grid: Grid) -> bool:
    """Check that no row, column, or box contains a repeated digit.

    Args:
        grid: A 9x9 grid; zeros are ignored.

    Returns:
        True when the filled cells are consistent with the rules.
    """
    for row in range(SIZE):
        for col in range(SIZE):
            value = grid[row][col]
            if value and any(grid[r][c] == value for r, c in _units(row, col)):
                return False
    return True


def is_solved(grid: Grid) -> bool:
    """Return True when every cell is filled and the grid is valid.

    Args:
        grid: The grid to check.

    Returns:
        Whether the grid is a complete solution.
    """
    return all(all(row) for row in grid) and is_valid(grid)


def candidates(grid: Grid, row: int, col: int) -> set[int]:
    """Return the digits that could legally go in an empty cell.

    Args:
        grid: The grid.
        row: Row index 0-8.
        col: Column index 0-8.

    Returns:
        The legal digits, or an empty set if the cell is already filled.
    """
    if grid[row][col]:
        return set()
    return set(DIGITS - {grid[r][c] for r, c in _units(row, col)})


def _propagate(grid: Grid) -> bool:
    """Fill naked singles in place until none remain.

    Returns:
        False if some empty cell has no candidates (a contradiction), otherwise True.
    """
    changed = True
    while changed:
        changed = False
        for row in range(SIZE):
            for col in range(SIZE):
                if grid[row][col]:
                    continue
                options = candidates(grid, row, col)
                if not options:
                    return False
                if len(options) == 1:
                    grid[row][col] = options.pop()
                    changed = True
    return True


def _best_cell(grid: Grid) -> tuple[int, int, set[int]] | None:
    """Return the empty cell with the fewest candidates (MRV heuristic), or None if the grid is full."""
    best: tuple[int, int, set[int]] | None = None
    for row in range(SIZE):
        for col in range(SIZE):
            if grid[row][col] == 0:
                options = candidates(grid, row, col)
                if best is None or len(options) < len(best[2]):
                    best = (row, col, options)
    return best


def _search(grid: Grid, limit: int, found: list[Grid]) -> None:
    """Depth-first search that appends up to ``limit`` solutions to ``found``."""
    if not _propagate(grid):
        return
    cell = _best_cell(grid)
    if cell is None:
        found.append([row[:] for row in grid])
        return
    row, col, options = cell
    for digit in sorted(options):
        if len(found) >= limit:
            return
        attempt = [r[:] for r in grid]
        attempt[row][col] = digit
        _search(attempt, limit, found)


def solve(grid: Grid) -> Grid | None:
    """Solve a sudoku without modifying the input.

    Args:
        grid: The puzzle, with 0 for empty cells.

    Returns:
        A solved copy of the grid, or None if the puzzle has no solution.
    """
    if not is_valid(grid):
        return None
    found: list[Grid] = []
    _search([row[:] for row in grid], 1, found)
    return found[0] if found else None


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count the puzzle's solutions, stopping once ``limit`` are found.

    A well-formed puzzle has exactly one solution, so ``count_solutions(grid) == 1`` checks uniqueness.

    Args:
        grid: The puzzle.
        limit: Maximum number of solutions to look for.

    Returns:
        The number of solutions found, at most ``limit``.
    """
    if limit < 1 or not is_valid(grid):
        return 0
    found: list[Grid] = []
    _search([row[:] for row in grid], limit, found)
    return len(found)
