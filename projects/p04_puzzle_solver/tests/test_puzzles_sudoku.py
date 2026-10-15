"""Milestone 1: sudoku parsing, validation, solving, and uniqueness."""

import pytest
from puzzles import sudoku

PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
HARD = "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."


def grid_of(text: str) -> sudoku.Grid:
    return sudoku.parse_grid(text)


def test_parse_single_line() -> None:
    grid = grid_of(PUZZLE)
    assert len(grid) == 9 and all(len(row) == 9 for row in grid), "parse_grid should return 9 rows of 9 cells"
    assert grid[0][:5] == [5, 3, 0, 0, 7], "'.' should become 0 and digits stay digits"


def test_parse_pretty_grid_with_zeros_and_separators() -> None:
    lines = [PUZZLE[i : i + 9].replace(".", "0") for i in range(0, 81, 9)]
    pretty = "\n".join(f"{r[:3]} | {r[3:6]} | {r[6:]}" for r in lines)
    assert grid_of(pretty) == grid_of(PUZZLE), "whitespace, '|' and zeros should parse the same as the compact form"


@pytest.mark.parametrize("text", [PUZZLE[:-1], PUZZLE + "1", PUZZLE[:-1] + "x"])
def test_parse_rejects_bad_input(text: str) -> None:
    with pytest.raises(sudoku.SudokuError):
        sudoku.parse_grid(text)


def test_sudoku_error_is_value_error() -> None:
    assert issubclass(sudoku.SudokuError, ValueError), "SudokuError should subclass ValueError"


def test_format_grid_round_trips() -> None:
    grid = grid_of(PUZZLE)
    text = sudoku.format_grid(grid)
    assert text.splitlines()[0] == "53..7....", "empty cells should render as '.'"
    assert grid_of(text) == grid, "format_grid output should parse back to the same grid"


def test_is_valid_accepts_puzzle_and_rejects_duplicates() -> None:
    assert sudoku.is_valid(grid_of(PUZZLE)), "the classic puzzle is valid"
    row_dup = grid_of("55" + PUZZLE[2:])
    assert not sudoku.is_valid(row_dup), "two 5s in row 0 must be invalid"
    box_dup = grid_of(PUZZLE[:10] + "5" + PUZZLE[11:])
    assert not sudoku.is_valid(box_dup), "two 5s in the top-left box must be invalid"


def test_candidates() -> None:
    grid = grid_of(PUZZLE)
    assert sudoku.candidates(grid, 0, 2) == {1, 2, 4}, "row 0 col 2 can only hold 1, 2 or 4"
    assert sudoku.candidates(grid, 0, 0) == set(), "a filled cell has no candidates"


def test_solve_classic_puzzle() -> None:
    grid = grid_of(PUZZLE)
    solved = sudoku.solve(grid)
    assert solved is not None, "the classic puzzle is solvable"
    assert "".join(str(v) for row in solved for v in row) == SOLUTION, "solution should match the known answer"
    assert grid == grid_of(PUZZLE), "solve must not modify its input"


def test_solve_hard_puzzle_keeps_givens() -> None:
    grid = grid_of(HARD)
    solved = sudoku.solve(grid)
    assert solved is not None and sudoku.is_solved(solved), "the hard puzzle should be solved completely"
    for r in range(9):
        for c in range(9):
            if grid[r][c]:
                assert solved[r][c] == grid[r][c], f"given at ({r}, {c}) must be kept"


def test_solve_detects_invalid_board() -> None:
    assert sudoku.solve(grid_of("55" + PUZZLE[2:])) is None, "a board that breaks the rules has no solution"


def test_solve_detects_unsolvable_but_valid_board() -> None:
    # Row 0 has 1-8 and the 9 is blocked by a 9 in column 8 lower down, so cell (0, 8) has no candidate.
    text = "12345678." + "........9" + "." * 63
    grid = grid_of(text)
    assert sudoku.is_valid(grid), "the board has no duplicates"
    assert sudoku.solve(grid) is None, "cell (0, 8) has no legal digit, so solve must return None"
    assert sudoku.count_solutions(grid) == 0, "an unsolvable board has zero solutions"


def test_is_solved() -> None:
    assert sudoku.is_solved(grid_of(SOLUTION)), "the known solution is solved"
    assert not sudoku.is_solved(grid_of(PUZZLE)), "a grid with blanks is not solved"


def test_count_solutions_unique() -> None:
    assert sudoku.count_solutions(grid_of(PUZZLE)) == 1, "the classic puzzle has a unique solution"


def test_count_solutions_respects_limit() -> None:
    empty = grid_of("." * 81)
    assert sudoku.count_solutions(empty, limit=3) == 3, "an empty grid has many solutions; stop at the limit"
    assert sudoku.count_solutions(empty, limit=1) == 1, "limit=1 should stop after the first solution"


def _swappable_rectangle(grid: sudoku.Grid) -> list[tuple[int, int]] | None:
    """Find four cells x/y over y/x spanning exactly two boxes, so blanking them leaves two solutions."""
    for r1 in range(9):
        for r2 in range(r1 + 1, 9):
            for c1 in range(9):
                for c2 in range(c1 + 1, 9):
                    x, y = grid[r1][c1], grid[r1][c2]
                    same_band, same_stack = r1 // 3 == r2 // 3, c1 // 3 == c2 // 3
                    if grid[r2][c1] == y and grid[r2][c2] == x and same_band != same_stack:
                        return [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
    return None


def test_count_solutions_non_unique_puzzle() -> None:
    grid = grid_of(SOLUTION)
    cells = _swappable_rectangle(grid)
    assert cells is not None, "test setup: the known solution should contain a swappable rectangle"
    for r, c in cells:
        grid[r][c] = 0
    assert sudoku.count_solutions(grid, limit=5) == 2, "a swappable rectangle gives exactly two solutions"
