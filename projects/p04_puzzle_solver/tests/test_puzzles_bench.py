"""Milestone 6: the benchmark CLI."""

import pytest
from puzzles import bench


def test_benchmarks_run_and_return_results() -> None:
    names = bench.benchmarks()
    assert {"sudoku", "word_ladder", "maze", "sliding", "knapsack", "intervals"} <= set(names), "all solvers covered"
    for name, func in names.items():
        assert func() is not None, f"benchmark {name!r} should return its solver's result"


def test_time_call_is_positive() -> None:
    assert bench.time_call(lambda: sum(range(100)), repeat=2) >= 0.0, "a timing is a non-negative float"


def test_main_prints_a_row_per_solver(capsys: pytest.CaptureFixture[str]) -> None:
    assert bench.main(["--repeat", "1"]) == 0, "main returns exit code 0"
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].split()[0] == "solver", "the first line is a header"
    assert len(lines) == len(bench.benchmarks()) + 1, "one row per benchmark plus the header"
    for line in lines[1:]:
        assert float(line.split()[-1]) >= 0.0, "each row ends with a millisecond timing"


def test_main_only_filters(capsys: pytest.CaptureFixture[str]) -> None:
    bench.main(["--repeat", "1", "--only", "knapsack"])
    lines = capsys.readouterr().out.strip().splitlines()
    assert [line.split()[0] for line in lines[1:]] == ["knapsack"], "--only limits the rows"
