"""Word ladders: shortest single-letter transformations with breadth-first search."""

import string
from collections import deque
from collections.abc import Iterable


def neighbors(word: str, words: set[str]) -> list[str]:
    """Return the dictionary words that differ from ``word`` in exactly one position.

    Args:
        word: The current word.
        words: The dictionary.

    Returns:
        Matching words in sorted order.
    """
    found: set[str] = set()
    for i, original in enumerate(word):
        for letter in string.ascii_lowercase:
            if letter != original:
                candidate = word[:i] + letter + word[i + 1 :]
                if candidate in words:
                    found.add(candidate)
    return sorted(found)


def _path(parents: dict[str, str | None], end: str) -> list[str]:
    """Walk parent links back from ``end`` and return the path from the root."""
    path: list[str] = []
    node: str | None = end
    while node is not None:
        path.append(node)
        node = parents[node]
    return path[::-1]


def _bfs(start: str, end: str, words: set[str]) -> list[str] | None:
    parents: dict[str, str | None] = {start: None}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        for nxt in neighbors(word, words):
            if nxt not in parents:
                parents[nxt] = word
                if nxt == end:
                    return _path(parents, end)
                queue.append(nxt)
    return None


def _expand(
    layer: list[str], own: dict[str, str | None], other: dict[str, str | None], words: set[str]
) -> tuple[list[str], str | None]:
    """Expand one BFS layer; return the next layer and the first word also reached from the other side."""
    next_layer: list[str] = []
    for word in layer:
        for nxt in neighbors(word, words):
            if nxt in own:
                continue
            own[nxt] = word
            if nxt in other:
                return next_layer, nxt
            next_layer.append(nxt)
    return next_layer, None


def _bidirectional(start: str, end: str, words: set[str]) -> list[str] | None:
    front: dict[str, str | None] = {start: None}
    back: dict[str, str | None] = {end: None}
    front_layer, back_layer = [start], [end]
    while front_layer and back_layer:
        if len(front_layer) <= len(back_layer):
            front_layer, meeting = _expand(front_layer, front, back, words)
        else:
            back_layer, meeting = _expand(back_layer, back, front, words)
        if meeting is not None:
            return _path(front, meeting) + _path(back, meeting)[::-1][1:]
    return None


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
    start, end = start.lower(), end.lower()
    dictionary = {w.lower() for w in words if len(w) == len(start)}
    if len(start) != len(end) or end not in dictionary:
        return None
    if start == end:
        return [start]
    dictionary.add(start)
    return _bidirectional(start, end, dictionary) if bidirectional else _bfs(start, end, dictionary)
