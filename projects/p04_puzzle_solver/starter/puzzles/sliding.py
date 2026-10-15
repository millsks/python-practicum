"""The 8-puzzle: solvability by inversion parity and optimal solving with A*."""

from collections.abc import Sequence

Board = tuple[int, ...]

SIDE = 3
GOAL: Board = (1, 2, 3, 4, 5, 6, 7, 8, 0)
MOVES = {"U": -SIDE, "D": SIDE, "L": -1, "R": 1}


def make_board(tiles: Sequence[int]) -> Board:
    """Validate tiles and return them as a board tuple.

    Args:
        tiles: Nine numbers, a permutation of 0-8, read row by row; 0 is the blank.

    Returns:
        The board as a tuple.

    Raises:
        ValueError: If ``tiles`` is not a permutation of 0-8.
    """
    # TODO: Convert to a tuple and check sorted(board) == list(range(9)).
    raise NotImplementedError


def inversions(board: Board) -> int:
    """Count pairs of tiles (ignoring the blank) that appear in the wrong relative order.

    Args:
        board: The board.

    Returns:
        The inversion count.
    """
    # TODO: Drop the 0, then count pairs i < j with tiles[i] > tiles[j].
    raise NotImplementedError


def is_solvable(board: Board) -> bool:
    """Decide whether ``board`` can reach :data:`GOAL`.

    On an odd-width board every move changes the inversion count by an even amount (0 or 2), so parity is
    invariant and only boards with an even inversion count are solvable.

    Args:
        board: The board.

    Returns:
        True when the board is solvable.
    """
    # TODO: On a 3x3 board the puzzle is solvable exactly when the inversion count is even.
    raise NotImplementedError


def manhattan(board: Board) -> int:
    """Sum each tile's grid distance from its goal position.

    Args:
        board: The board.

    Returns:
        The Manhattan heuristic, which never overestimates the remaining moves.
    """
    # TODO: abs(row difference) + abs(column difference).
    raise NotImplementedError


def apply_move(board: Board, move: str) -> Board | None:
    """Slide the blank in direction ``move``.

    Args:
        board: The board.
        move: One of ``U``, ``D``, ``L``, ``R`` (the direction the blank moves).

    Returns:
        The new board, or None when the move would leave the grid.
    """
    # TODO: Find the blank, return None if the move leaves the grid, else swap it with its neighbor.
    raise NotImplementedError


def apply_moves(board: Board, moves: str | Sequence[str]) -> Board:
    """Apply a sequence of moves.

    Args:
        board: Starting board.
        moves: Move letters.

    Returns:
        The resulting board.

    Raises:
        ValueError: If a move is unknown or illegal from the current position.
    """
    # TODO: Apply each move in turn; raise ValueError for an unknown or illegal move.
    raise NotImplementedError


def solve(board: Sequence[int]) -> str | None:
    """Find a shortest sequence of blank moves that solves the puzzle.

    Args:
        board: The starting tiles.

    Returns:
        A string of move letters (empty when already solved), or None if the board is unsolvable.
    """
    # TODO: Return None for an invalid board. Work on a copy so the input is unchanged.
    # TODO: Backtracking: propagate naked singles, pick the empty cell with the fewest candidates (MRV),
    # TODO: try each candidate on a copy, and recurse. A cell with zero candidates means backtrack.
    raise NotImplementedError
