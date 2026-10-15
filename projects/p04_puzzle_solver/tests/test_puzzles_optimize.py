"""Milestone 5: 0/1 knapsack and weighted interval scheduling."""

import itertools
import random

import pytest
from puzzles import optimize


def brute_knapsack(items: list[tuple[int, int]], capacity: int) -> int:
    best = 0
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            if sum(w for w, _ in combo) <= capacity:
                best = max(best, sum(v for _, v in combo))
    return best


def brute_intervals(intervals: list[tuple[int, int, int]]) -> int:
    best = 0
    for r in range(len(intervals) + 1):
        for combo in itertools.combinations(sorted(intervals, key=lambda t: t[0]), r):
            if all(a[1] <= b[0] for a, b in itertools.pairwise(combo)):
                best = max(best, sum(t[2] for t in combo))
    return best


def test_knapsack_textbook_example() -> None:
    items = [(12, 4), (2, 2), (1, 1), (1, 2), (4, 10)]
    assert optimize.knapsack(items, 15) == (15, [1, 2, 3, 4]), "take every item except the heavy one"


def test_knapsack_reconstruction_is_consistent() -> None:
    items = [(1, 1), (3, 4), (4, 5), (5, 7)]
    value, chosen = optimize.knapsack(items, 7)
    assert value == 9, "best value for capacity 7 is 9 (weights 3 + 4)"
    assert sum(items[i][0] for i in chosen) <= 7, "chosen items must fit"
    assert sum(items[i][1] for i in chosen) == value, "chosen items must add up to the reported value"


def test_knapsack_edge_cases() -> None:
    assert optimize.knapsack([], 10) == (0, []), "no items gives value 0"
    assert optimize.knapsack([(5, 10)], 4) == (0, []), "an item heavier than the capacity is skipped"
    assert optimize.knapsack([(5, 10)], 0) == (0, []), "capacity 0 holds nothing"
    with pytest.raises(ValueError):
        optimize.knapsack([(1, 1)], -1)


def test_knapsack_matches_brute_force() -> None:
    rng = random.Random(7)
    for _ in range(25):
        items = [(rng.randint(1, 10), rng.randint(0, 20)) for _ in range(rng.randint(0, 8))]
        capacity = rng.randint(0, 25)
        value, chosen = optimize.knapsack(items, capacity)
        assert value == brute_knapsack(items, capacity), f"knapsack({items}, {capacity}) is not optimal"
        assert sum(items[i][0] for i in chosen) <= capacity, "chosen items exceed the capacity"
        assert sum(items[i][1] for i in chosen) == value, "chosen items do not match the value"
        assert chosen == sorted(set(chosen)), "indexes must be unique and ascending"


def test_intervals_example() -> None:
    intervals = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 9, 3), (6, 10, 2), (8, 11, 4)]
    assert optimize.weighted_interval_scheduling(intervals) == (13, [0, 3, 7]), "(1,4)+(4,7)+(8,11) weighs 13"


def test_intervals_touching_are_compatible() -> None:
    assert optimize.weighted_interval_scheduling([(1, 3, 2), (3, 5, 2)]) == (4, [0, 1]), "half-open: 3 == 3 is fine"


def test_intervals_heavy_beats_many_light() -> None:
    result = optimize.weighted_interval_scheduling([(0, 10, 50), (0, 2, 5), (2, 4, 5), (4, 6, 5)])
    assert result == (50, [0]), "one heavy interval beats three light ones"


def test_intervals_edge_cases() -> None:
    assert optimize.weighted_interval_scheduling([]) == (0, []), "no intervals gives weight 0"
    with pytest.raises(ValueError):
        optimize.weighted_interval_scheduling([(5, 1, 3)])


def test_intervals_match_brute_force() -> None:
    rng = random.Random(11)
    for _ in range(25):
        intervals = []
        for _ in range(rng.randint(0, 8)):
            start = rng.randint(0, 15)
            intervals.append((start, start + rng.randint(1, 6), rng.randint(1, 20)))
        weight, chosen = optimize.weighted_interval_scheduling(intervals)
        assert weight == brute_intervals(intervals), f"schedule for {intervals} is not optimal"
        picked = sorted((intervals[i] for i in chosen), key=lambda t: t[0])
        assert all(a[1] <= b[0] for a, b in itertools.pairwise(picked)), "chosen intervals overlap"
        assert sum(t[2] for t in picked) == weight, "chosen intervals do not add up to the weight"
