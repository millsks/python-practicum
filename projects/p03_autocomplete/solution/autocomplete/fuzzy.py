"""Typo tolerance: Levenshtein distance and a pruned search over a trie."""

from autocomplete.trie import Trie, TrieNode


def levenshtein(a: str, b: str) -> int:
    """Return the edit distance between two strings.

    Insertions, deletions, and substitutions each cost 1.

    Args:
        a: First string.
        b: Second string.

    Returns:
        The minimum number of single-character edits turning ``a`` into ``b``.
    """
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (char_a != char_b)))
        previous = current
    return previous[-1]


def within_distance(a: str, b: str, max_distance: int) -> bool:
    """Return whether ``levenshtein(a, b) <= max_distance``, stopping early when it cannot be.

    Args:
        a: First string.
        b: Second string.
        max_distance: The largest allowed distance.

    Returns:
        ``True`` when the strings are within ``max_distance`` edits.
    """
    if abs(len(a) - len(b)) > max_distance:
        return False
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (char_a != char_b)))
        if min(current) > max_distance:
            return False
        previous = current
    return previous[-1] <= max_distance


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
    if max_distance < 0:
        raise ValueError("max_distance must be non-negative")
    results: list[tuple[str, int]] = []
    first_row = list(range(len(query) + 1))

    def visit(node: TrieNode, text: str, previous: list[int]) -> None:
        if node.is_word and previous[-1] <= max_distance:
            results.append((text, previous[-1]))
        for char, child in node.children.items():
            row = [previous[0] + 1]
            for j, query_char in enumerate(query, start=1):
                row.append(min(row[j - 1] + 1, previous[j] + 1, previous[j - 1] + (query_char != char)))
            if min(row) <= max_distance:
                visit(child, text + char, row)

    visit(trie.root, "", first_row)
    results.sort(key=lambda pair: (pair[1], pair[0]))
    return results
