"""Benchmark CLI: time every solver on built-in puzzles and print a table."""

from collections.abc import Callable, Sequence

from puzzles import maze, optimize, sliding, sudoku, word_ladder

SUDOKU = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
WORDS = ["hot", "dot", "dog", "lot", "log", "cog", "cot", "hog"]
MAZE = """
#########
#S..#...#
#.#.#.#.#
#.#...#G#
#########
"""
EIGHT = (8, 6, 7, 2, 5, 4, 3, 0, 1)
ITEMS = [(12, 4), (2, 2), (1, 1), (1, 2), (4, 10)]
INTERVALS = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 9, 3), (6, 10, 2), (8, 11, 4)]


def benchmarks() -> dict[str, Callable[[], object]]:
    """Return the named benchmark callables.

    Returns:
        A mapping from benchmark name to a zero-argument function that runs one solve.
    """
    return {
        "sudoku": lambda: sudoku.solve(sudoku.parse_grid(SUDOKU)),
        "word_ladder": lambda: word_ladder.ladder("hit", "cog", WORDS),
        "word_ladder_bidir": lambda: word_ladder.ladder("hit", "cog", WORDS, bidirectional=True),
        "maze": lambda: maze.solve_maze(maze.parse_maze(MAZE)),
        "sliding": lambda: sliding.solve(EIGHT),
        "knapsack": lambda: optimize.knapsack(ITEMS, 15),
        "intervals": lambda: optimize.weighted_interval_scheduling(INTERVALS),
    }


def time_call(func: Callable[[], object], repeat: int) -> float:
    """Return the best wall-clock time in seconds over ``repeat`` runs.

    Args:
        func: The function to time.
        repeat: Number of runs (at least 1).

    Returns:
        The fastest run in seconds.
    """
    # TODO: Run func `repeat` times (at least once) with time.perf_counter() and return the fastest.
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmarks and print one ``name  milliseconds`` line per solver.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        The process exit code.
    """
    # TODO: argparse with --repeat (int, default 3) and --only (repeatable choice of benchmark names).
    # TODO: Print a header line starting with 'solver', then one '<name>  <best ms>' row per benchmark.
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
