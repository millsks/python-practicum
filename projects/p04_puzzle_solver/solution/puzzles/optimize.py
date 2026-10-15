"""Dynamic programming for packing and scheduling: 0/1 knapsack and weighted interval scheduling."""

from bisect import bisect_right
from collections.abc import Sequence


def knapsack(items: Sequence[tuple[int, int]], capacity: int) -> tuple[int, list[int]]:
    """Choose items maximizing total value within a weight capacity (each item used at most once).

    ``best[i][w]`` is the best value using the first ``i`` items with capacity ``w``; the chosen items are
    recovered by walking the table backwards.

    Args:
        items: ``(weight, value)`` pairs with non-negative integers.
        capacity: Maximum total weight.

    Returns:
        ``(best_value, indexes)`` with the chosen item indexes in ascending order.

    Raises:
        ValueError: If the capacity or any weight or value is negative.
    """
    if capacity < 0 or any(w < 0 or v < 0 for w, v in items):
        raise ValueError("capacity, weights, and values must be non-negative")
    n = len(items)
    best = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i, (weight, value) in enumerate(items, start=1):
        previous, row = best[i - 1], best[i]
        for w in range(capacity + 1):
            row[w] = previous[w]
            if weight <= w and previous[w - weight] + value > row[w]:
                row[w] = previous[w - weight] + value
    chosen: list[int] = []
    w = capacity
    for i in range(n, 0, -1):
        if best[i][w] != best[i - 1][w]:
            chosen.append(i - 1)
            w -= items[i - 1][0]
    return best[n][capacity], sorted(chosen)


def weighted_interval_scheduling(intervals: Sequence[tuple[int, int, int]]) -> tuple[int, list[int]]:
    """Pick non-overlapping intervals with the largest total weight.

    Intervals are half-open, so ``(1, 3)`` and ``(3, 5)`` are compatible. After sorting by end time,
    ``best[j] = max(best[j - 1], weight_j + best[p(j)])`` where ``p(j)`` (found with :func:`bisect.bisect_right`)
    counts the intervals that end no later than interval ``j`` starts.

    Args:
        intervals: ``(start, end, weight)`` triples with ``start <= end``.

    Returns:
        ``(best_weight, indexes)`` with the chosen indexes (into ``intervals``) in ascending order.

    Raises:
        ValueError: If an interval ends before it starts.
    """
    if any(end < start for start, end, _ in intervals):
        raise ValueError("every interval needs start <= end")
    order = sorted(range(len(intervals)), key=lambda i: intervals[i][1])
    ends = [intervals[i][1] for i in order]
    best = [0] * (len(order) + 1)
    compatible = [0] * len(order)
    for j, index in enumerate(order, start=1):
        start, _, weight = intervals[index]
        compatible[j - 1] = bisect_right(ends, start, 0, j - 1)
        best[j] = max(best[j - 1], weight + best[compatible[j - 1]])
    chosen: list[int] = []
    j = len(order)
    while j > 0:
        if best[j] != best[j - 1]:
            chosen.append(order[j - 1])
            j = compatible[j - 1]
        else:
            j -= 1
    return best[-1], sorted(chosen)
