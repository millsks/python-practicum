"""Typo tolerance: Levenshtein distance and a pruned search over a trie."""

from autocomplete.trie import Trie


def levenshtein(a: str, b: str) -> int:
    """Return the edit distance between two strings.

    Insertions, deletions, and substitutions each cost 1.

    Args:
        a: First string.
        b: Second string.

    Returns:
        The minimum number of single-character edits turning ``a`` into ``b``.
    """
    # TODO(milestone 4): the classic dynamic-programming table, kept to two rows of length len(b) + 1.
    raise NotImplementedError


def within_distance(a: str, b: str, max_distance: int) -> bool:
    """Return whether ``levenshtein(a, b) <= max_distance``, stopping early when it cannot be.

    Args:
        a: First string.
        b: Second string.
        max_distance: The largest allowed distance.

    Returns:
        ``True`` when the strings are within ``max_distance`` edits.
    """
    # TODO(milestone 4): fail fast on a length gap; stop as soon as min(row) exceeds the bound.
    raise NotImplementedError


def fuzzy_search(trie: Trie, query: str, max_distance: int) -> list[tuple[str, int]]:
    """Find stored terms within ``max_distance`` edits of ``query``.

    Walks the trie computing one Levenshtein row per node; a branch is abandoned as soon as
    every entry in its row exceeds ``max_distance``, because no longer term can do better.

    Args:
        trie: The trie to search.
        query: The (possibly misspelled) term.
        max_distance: The largest allowed edit distance; must be non-negative.

    Returns:
        ``(term, distance)`` pairs sorted by distance, then term.

    Raises:
        ValueError: If ``max_distance`` is negative.
    """
    # TODO(milestone 4): start from row = list(range(len(query) + 1)) at trie.root. For each child character,
    # build the next row from the parent's row; recurse only if min(row) <= max_distance. A node that is a
    # word and whose row[-1] <= max_distance is a match.
    raise NotImplementedError
