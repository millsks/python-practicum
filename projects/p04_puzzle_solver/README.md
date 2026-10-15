# Project 4: Puzzle Solver Suite

Closes Part 4 (Algorithms). Full brief with diagrams, rubric, and hints: `docs/projects/p04-puzzle-solver.html`.

## Scenario

Brainteaser Studio ships a puzzle app with daily sudoku, word ladders, mazes, and sliding-tile puzzles. Its level
designers need solvers they can trust: a sudoku generator must know whether a board has exactly one solution, the
maze editor must report the cheapest route over rough terrain, and the hint button on the 8-puzzle must suggest a
move on an optimal path. You will build the `puzzles` package that powers all of it, plus a small benchmark CLI.

## Modules

| Module | What it does | Techniques (module) |
|---|---|---|
| `puzzles.sudoku` | parse/validate a grid, solve, detect unsolvable boards, count solutions up to a limit | backtracking, constraint propagation, MRV (M33) |
| `puzzles.word_ladder` | shortest one-letter transformation with path reconstruction, optional bidirectional BFS | BFS (M26, M31) |
| `puzzles.maze` | parse an ASCII maze with weighted cells; A* with a Manhattan heuristic | A*, heaps (M31) |
| `puzzles.sliding` | 8-puzzle solvability by inversion parity; optimal A* solve | invariants (M34), A* (M31) |
| `puzzles.optimize` | 0/1 knapsack with item reconstruction; weighted interval scheduling | DP, `bisect` (M32, M30) |
| `puzzles.bench` | `main()` CLI printing best-of-N timings for every solver | `time.perf_counter`, `argparse` |

## Start and grade

```bash
pixi run start p04          # copies starter/ to work/p04_puzzle_solver/
pixi run grade p04          # runs the tests against your work/ copy
cd work/p04_puzzle_solver && pixi run python -m puzzles.bench --repeat 5
```

Every public function in `starter/puzzles/` has its signature, type hints, docstring, and TODO comments. Replace each
`raise NotImplementedError`. Add private helpers freely; keep the public signatures.

## Milestones

1. **Sudoku** (`tests/test_puzzles_sudoku.py`): `parse_grid`, `format_grid`, `is_valid`, `is_solved`, `candidates`,
   `solve`, `count_solutions`.
2. **Word ladder** (`test_puzzles_word_ladder.py`): `neighbors`, `ladder(..., bidirectional=False|True)`.
3. **Maze** (`test_puzzles_maze.py`): `parse_maze`, `Maze.cost`, `Maze.neighbors`, `manhattan`, `solve_maze`,
   `render_path`.
4. **Sliding puzzle** (`test_puzzles_sliding.py`): `make_board`, `inversions`, `is_solvable`, `manhattan`,
   `apply_move`, `apply_moves`, `solve`.
5. **Knapsack and scheduling** (`test_puzzles_optimize.py`): `knapsack`, `weighted_interval_scheduling`.
6. **Benchmark CLI** (`test_puzzles_bench.py`): `time_call`, `main`.

Grade one milestone at a time: `pixi run grade p04 -- -k sudoku`.

## Stretch goals

- Sudoku: add hidden singles (a digit that fits only one cell of a unit) and measure how many guesses it saves.
- Word ladder: return *all* shortest ladders.
- Maze: allow diagonal moves and switch to the Chebyshev or octile heuristic; prove it stays admissible.
- Sliding: generalize to the 15-puzzle (parity rule changes on even widths) and try IDA* to save memory.
- Benchmark: add `--json` output and a comparison of BFS vs bidirectional BFS on a large word list.
