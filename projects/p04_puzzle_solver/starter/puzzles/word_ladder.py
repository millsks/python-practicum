"""Word ladders: shortest single-letter transformations with breadth-first search."""

from collections.abc import Iterable


def neighbors(word: str, words: set[str]) -> list[str]:
    """Return the dictionary words that differ from ``word`` in exactly one position.

    Args:
        word: The current word.
        words: The dictionary.

    Returns:
        Matching words in sorted order.
    """
    # TODO: Try every position and every letter a-z; keep candidates that are in `words`, sorted.
    raise NotImplementedError


def ladder(start: str, end: str, words: Iterable[str], *, bidirectional: bool = False) -> list[str] | None:
    """Find a shortest word ladder from ``start`` to ``end``.

    Each step changes one letter and every intermediate word (and ``end``) must be in ``words``. ``start``
    does not need to be in the dictionary. Comparisons are case-insensitive; results are lowercase.

    Args:
        start: First word.
        end: Target word.
        words: The dictionary.
        bidirectional: Search from both ends at once, which explores far fewer words on large dictionaries.

    Returns:
        The ladder including both ends, or None if no ladder exists.
    """
    # TODO: Lowercase everything, keep only same-length words, and return None if `end` is missing.
    # TODO: Plain BFS: a deque, a parents dict, and path reconstruction by walking parents back from end.
    # TODO: Bidirectional: grow two parent dicts one layer at a time (expand the smaller frontier) until
    # TODO: they meet, then join the two half-paths.
    raise NotImplementedError
