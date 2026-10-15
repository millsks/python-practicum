"""Milestone 4: the 8-puzzle with inversion parity and A*."""

import random
from collections import deque

import pytest
from puzzles import sliding


def bfs_distance(board: sliding.Board, limit: int = 12) -> int | None:
    seen = {board}
    queue = deque([(board, 0)])
    while queue:
        current, dist = queue.popleft()
        if current == sliding.GOAL:
            return dist
        if dist == limit:
            continue
        for move in "UDLR":
            nxt = sliding.apply_move(current, move)
            if nxt is not None and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, dist + 1))
    return None


def test_make_board_validates() -> None:
    assert sliding.make_board([1, 2, 3, 4, 5, 6, 7, 8, 0]) == sliding.GOAL, "a list becomes a tuple board"
    with pytest.raises(ValueError):
        sliding.make_board([1, 1, 3, 4, 5, 6, 7, 8, 0])
    with pytest.raises(ValueError):
        sliding.make_board([1, 2, 3])


def test_inversions_and_solvability() -> None:
    assert sliding.inversions(sliding.GOAL) == 0, "the goal has no inversions"
    swapped = (2, 1, 3, 4, 5, 6, 7, 8, 0)
    assert sliding.inversions(swapped) == 1, "swapping two tiles creates one inversion"
    assert not sliding.is_solvable(swapped), "odd inversions are unsolvable on a 3x3 board"
    assert sliding.is_solvable((8, 6, 7, 2, 5, 4, 3, 0, 1)), "the hardest 8-puzzle is still solvable"


def test_manhattan_heuristic() -> None:
    assert sliding.manhattan(sliding.GOAL) == 0, "the goal has heuristic 0"
    assert sliding.manhattan((1, 2, 3, 4, 5, 6, 7, 0, 8)) == 1, "one tile one step away"
    assert sliding.manhattan((8, 6, 7, 2, 5, 4, 3, 0, 1)) == 21, "known Manhattan value of the hardest board"


def test_apply_move_edges() -> None:
    assert sliding.apply_move(sliding.GOAL, "D") is None, "the blank in the bottom row cannot move down"
    assert sliding.apply_move(sliding.GOAL, "R") is None, "the blank in the right column cannot move right"
    assert sliding.apply_move(sliding.GOAL, "L") == (1, 2, 3, 4, 5, 6, 7, 0, 8), "L swaps the blank with tile 8"
    with pytest.raises(ValueError):
        sliding.apply_moves(sliding.GOAL, "D")
    with pytest.raises(ValueError):
        sliding.apply_moves(sliding.GOAL, "X")


def test_solved_board_needs_no_moves() -> None:
    assert sliding.solve(sliding.GOAL) == "", "an already solved board returns an empty move string"


def test_unsolvable_returns_none() -> None:
    assert sliding.solve((2, 1, 3, 4, 5, 6, 7, 8, 0)) is None, "an unsolvable board returns None"


def test_known_short_puzzle() -> None:
    board = (1, 2, 3, 4, 5, 6, 0, 7, 8)
    moves = sliding.solve(board)
    assert moves == "RR", "the blank must move right twice"


def test_hardest_puzzle_is_31_moves() -> None:
    board = (8, 6, 7, 2, 5, 4, 3, 0, 1)
    moves = sliding.solve(board)
    assert moves is not None and len(moves) == 31, "this board's optimal solution is 31 moves"
    assert sliding.apply_moves(board, moves) == sliding.GOAL, "the moves must actually solve the board"


def test_random_scrambles_are_optimal() -> None:
    rng = random.Random(4)
    for _ in range(5):
        board = sliding.GOAL
        for _ in range(14):
            options = [b for m in "UDLR" if (b := sliding.apply_move(board, m)) is not None]
            board = rng.choice(options)
        moves = sliding.solve(board)
        assert moves is not None, "a scramble of the goal is always solvable"
        assert sliding.apply_moves(board, moves) == sliding.GOAL, "the moves must solve the scramble"
        assert len(moves) == bfs_distance(board, limit=14), "A* with Manhattan must match BFS's optimal length"
