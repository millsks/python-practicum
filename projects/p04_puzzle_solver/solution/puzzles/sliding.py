"""The 8-puzzle: solvability by inversion parity and optimal solving with A*."""

import heapq
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
    board = tuple(tiles)
    if sorted(board) != list(range(SIDE * SIDE)):
        raise ValueError(f"board must be a permutation of 0-8, got {board}")
    return board


def inversions(board: Board) -> int:
    """Count pairs of tiles (ignoring the blank) that appear in the wrong relative order.

    Args:
        board: The board.

    Returns:
        The inversion count.
    """
    tiles = [t for t in board if t]
    return sum(1 for i in range(len(tiles)) for j in range(i + 1, len(tiles)) if tiles[i] > tiles[j])


def is_solvable(board: Board) -> bool:
    """Decide whether ``board`` can reach :data:`GOAL`.

    On an odd-width board every move changes the inversion count by an even amount (0 or 2), so parity is
    invariant and only boards with an even inversion count are solvable.

    Args:
        board: The board.

    Returns:
        True when the board is solvable.
    """
    return inversions(make_board(board)) % 2 == 0


def manhattan(board: Board) -> int:
    """Sum each tile's grid distance from its goal position.

    Args:
        board: The board.

    Returns:
        The Manhattan heuristic, which never overestimates the remaining moves.
    """
    total = 0
    for index, tile in enumerate(board):
        if tile:
            goal = tile - 1
            total += abs(index // SIDE - goal // SIDE) + abs(index % SIDE - goal % SIDE)
    return total


def apply_move(board: Board, move: str) -> Board | None:
    """Slide the blank in direction ``move``.

    Args:
        board: The board.
        move: One of ``U``, ``D``, ``L``, ``R`` (the direction the blank moves).

    Returns:
        The new board, or None when the move would leave the grid.
    """
    blank = board.index(0)
    row, col = divmod(blank, SIDE)
    if (move == "U" and row == 0) or (move == "D" and row == SIDE - 1):
        return None
    if (move == "L" and col == 0) or (move == "R" and col == SIDE - 1):
        return None
    target = blank + MOVES[move]
    tiles = list(board)
    tiles[blank], tiles[target] = tiles[target], tiles[blank]
    return tuple(tiles)


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
    for move in moves:
        if move not in MOVES:
            raise ValueError(f"unknown move {move!r}")
        nxt = apply_move(board, move)
        if nxt is None:
            raise ValueError(f"illegal move {move!r} from {board}")
        board = nxt
    return board


def solve(board: Sequence[int]) -> str | None:
    """Find a shortest sequence of blank moves that solves the puzzle.

    Args:
        board: The starting tiles.

    Returns:
        A string of move letters (empty when already solved), or None if the board is unsolvable.
    """
    start = make_board(board)
    if not is_solvable(start):
        return None
    best: dict[Board, int] = {start: 0}
    parent: dict[Board, tuple[Board, str]] = {}
    counter = 0
    frontier: list[tuple[int, int, int, Board]] = [(manhattan(start), 0, counter, start)]
    while frontier:
        _, cost, _, current = heapq.heappop(frontier)
        if current == GOAL:
            moves: list[str] = []
            while current in parent:
                current, move = parent[current]
                moves.append(move)
            return "".join(reversed(moves))
        if cost > best[current]:
            continue
        for move in MOVES:
            nxt = apply_move(current, move)
            if nxt is not None and cost + 1 < best.get(nxt, cost + 2):
                best[nxt] = cost + 1
                parent[nxt] = (current, move)
                counter += 1
                heapq.heappush(frontier, (cost + 1 + manhattan(nxt), cost + 1, counter, nxt))
    return None
