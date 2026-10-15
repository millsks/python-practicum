"""Dynamic programming for packing and scheduling: 0/1 knapsack and weighted interval scheduling."""

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
    # TODO: Validate inputs. Fill best[i][w] = max(skip item i, take it if it fits).
    # TODO: Reconstruct by walking i from n down: if best[i][w] != best[i-1][w], item i-1 was taken.
    raise NotImplementedError


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
    # TODO: Sort indexes by end time. For each interval use bisect_right on the end
    # TODO: times to find how many earlier intervals are compatible (p(j)), then
    # TODO: best[j] = max(best[j-1], weight + best[p(j)]). Walk back to recover choices.
    raise NotImplementedError
