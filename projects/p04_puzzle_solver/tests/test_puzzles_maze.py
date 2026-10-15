"""Milestone 3: ASCII mazes with A* and weighted cells."""

import itertools
from collections import deque

import pytest
from puzzles import maze

SIMPLE = """
#########
#S..#...#
#.#.#.#.#
#.#...#G#
#########
"""

WEIGHTED = """
#######
#S999G#
#.###.#
#.....#
#######
"""


def bfs_steps(m: maze.Maze) -> int | None:
    seen = {m.start}
    queue = deque([(m.start, 0)])
    while queue:
        cell, dist = queue.popleft()
        if cell == m.goal:
            return dist
        for nxt, _ in m.neighbors(cell):
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, dist + 1))
    return None


def test_parse_finds_start_and_goal() -> None:
    m = maze.parse_maze(SIMPLE)
    assert m.start == (1, 1) and m.goal == (3, 7), "S and G positions are (row, col)"
    assert (m.height, m.width) == (5, 9), "the simple maze is 5 rows by 9 columns"


def test_parse_pads_ragged_rows_with_walls() -> None:
    m = maze.parse_maze("#####\n#S.G#\n###")
    assert m.width == 5 and m.rows[2] == "#####", "short rows are padded with walls"


@pytest.mark.parametrize("text", ["", "#S.#", "#G.#", "#SSG#", "#S?G#"])
def test_parse_rejects_bad_mazes(text: str) -> None:
    with pytest.raises(maze.MazeError):
        maze.parse_maze(text)


def test_cost_and_neighbors() -> None:
    m = maze.parse_maze(WEIGHTED)
    assert m.cost((0, 0)) is None, "walls cannot be entered"
    assert m.cost((1, 2)) == 9, "digit cells cost their value"
    assert m.cost((1, 1)) == 1 and m.cost((-1, 0)) is None, "S costs 1; off-board is None"
    assert sorted(m.neighbors((1, 1))) == [((1, 2), 9), ((2, 1), 1)], "neighbors skip walls and carry costs"


def test_manhattan() -> None:
    assert maze.manhattan((0, 0), (3, 4)) == 7, "Manhattan distance is |dr| + |dc|"


def test_simple_maze_shortest_path() -> None:
    m = maze.parse_maze(SIMPLE)
    result = maze.solve_maze(m)
    assert result is not None, "the simple maze is solvable"
    path, cost = result
    assert path[0] == m.start and path[-1] == m.goal, "the path runs from S to G"
    assert cost == len(path) - 1 == bfs_steps(m) == 12, "with unit costs A* must match BFS: 12 steps"
    for a, b in itertools.pairwise(path):
        assert maze.manhattan(a, b) == 1 and m.cost(b) is not None, "each step is to an adjacent open cell"


def test_weighted_maze_takes_cheaper_detour() -> None:
    result = maze.solve_maze(maze.parse_maze(WEIGHTED))
    assert result is not None, "the weighted maze is solvable"
    path, cost = result
    assert cost == 8, "going around (8 steps of cost 1) beats crossing the 9s (cost 28)"
    assert all(maze.parse_maze(WEIGHTED).cost(c) == 1 for c in path), "the cheapest path avoids weighted cells"


def test_weighted_cells_worth_crossing() -> None:
    m = maze.parse_maze("#######\n#S2.2G#\n#.###.#\n#.....#\n#######")
    result = maze.solve_maze(m)
    assert result is not None and result[1] == 6, "crossing 2 + 1 + 2 + G(1) = 6 beats the 8-step detour"


def test_unreachable_goal() -> None:
    assert maze.solve_maze(maze.parse_maze("#####\n#S#G#\n#####")) is None, "a walled-off goal is unreachable"


def test_start_next_to_goal() -> None:
    assert maze.solve_maze(maze.parse_maze("#SG#")) == ([(0, 1), (0, 2)], 1), "adjacent S and G cost one step"


def test_render_path() -> None:
    m = maze.parse_maze("#S.G#")
    result = maze.solve_maze(m)
    assert result is not None
    assert maze.render_path(m, result[0]) == "#S*G#", "path cells become '*' while S and G stay"
