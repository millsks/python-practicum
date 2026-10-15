"""Sudoku parsing, validation, and a backtracking solver with constraint propagation."""

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
    # TODO: Walk the characters: skip whitespace and '|-+', map '.' to 0, digits to ints, else raise.
    # TODO: Check you have exactly 81 cells, then slice them into 9 rows of 9.
    raise NotImplementedError


def format_grid(grid: Grid) -> str:
    """Render a grid as nine lines of digits, using ``.`` for empty cells.

    Args:
        grid: The grid to render.

    Returns:
        The text form, without a trailing newline.
    """
    # TODO: Join each row's digits, using '.' for 0, and join rows with newlines.
    raise NotImplementedError


def is_valid(grid: Grid) -> bool:
    """Check that no row, column, or box contains a repeated digit.

    Args:
        grid: A 9x9 grid; zeros are ignored.

    Returns:
        True when the filled cells are consistent with the rules.
    """
    # TODO: For every filled cell, make sure no peer (same row, column, or 3x3 box) holds the same digit.
    # TODO: A helper that yields a cell's peers keeps this and candidates() short.
    raise NotImplementedError


def is_solved(grid: Grid) -> bool:
    """Return True when every cell is filled and the grid is valid.

    Args:
        grid: The grid to check.

    Returns:
        Whether the grid is a complete solution.
    """
    # TODO: Every cell non-zero and is_valid(grid).
    raise NotImplementedError


def candidates(grid: Grid, row: int, col: int) -> set[int]:
    """Return the digits that could legally go in an empty cell.

    Args:
        grid: The grid.
        row: Row index 0-8.
        col: Column index 0-8.

    Returns:
        The legal digits, or an empty set if the cell is already filled.
    """
    # TODO: Return set() for a filled cell; otherwise the digits 1-9 minus the digits of its peers.
    raise NotImplementedError


def solve(grid: Grid) -> Grid | None:
    """Solve a sudoku without modifying the input.

    Args:
        grid: The puzzle, with 0 for empty cells.

    Returns:
        A solved copy of the grid, or None if the puzzle has no solution.
    """
    # TODO: Return None for an invalid board. Work on a copy so the input is unchanged.
    # TODO: Backtracking: propagate naked singles, pick the empty cell with the fewest candidates (MRV),
    # TODO: try each candidate on a copy, and recurse. A cell with zero candidates means backtrack.
    raise NotImplementedError


def count_solutions(grid: Grid, limit: int = 2) -> int:
    """Count the puzzle's solutions, stopping once ``limit`` are found.

    A well-formed puzzle has exactly one solution, so ``count_solutions(grid) == 1`` checks uniqueness.

    Args:
        grid: The puzzle.
        limit: Maximum number of solutions to look for.

    Returns:
        The number of solutions found, at most ``limit``.
    """
    # TODO: Reuse the same search as solve(), but collect solutions and stop at `limit`.
    raise NotImplementedError
