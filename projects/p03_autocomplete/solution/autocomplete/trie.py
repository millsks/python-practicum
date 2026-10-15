"""A prefix tree (trie) that stores terms with popularity scores."""

import heapq
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(slots=True)
class TrieNode:
    """One node of a trie.

    Attributes:
        children: Child nodes keyed by the next character.
        is_word: Whether the path from the root to this node spells a stored term.
        score: Popularity score of the term ending here (meaningful only when ``is_word``).
    """

    children: dict[str, "TrieNode"] = field(default_factory=dict)
    is_word: bool = False
    score: float = 0.0


class Trie:
    """A set of strings organized by shared prefixes, each with a popularity score.

    Lookups cost O(L) for a key of length L, independent of how many terms are stored.
    """

    def __init__(self) -> None:
        """Create an empty trie."""
        self.root = TrieNode()
        self._size = 0

    def insert(self, word: str, score: float = 0.0) -> None:
        """Add ``word`` or update its score if it is already present.

        Args:
            word: The term to store; must be non-empty.
            score: Its popularity score.

        Raises:
            ValueError: If ``word`` is empty.
        """
        if not word:
            raise ValueError("cannot insert an empty term")
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        if not node.is_word:
            node.is_word = True
            self._size += 1
        node.score = score

    def _find(self, prefix: str) -> TrieNode | None:
        node = self.root
        for char in prefix:
            child = node.children.get(char)
            if child is None:
                return None
            node = child
        return node

    def contains(self, word: str) -> bool:
        """Return whether ``word`` is a stored term (not merely a prefix).

        Args:
            word: The term to look up.

        Returns:
            ``True`` when the term was inserted and not deleted.
        """
        node = self._find(word)
        return node is not None and node.is_word

    def __contains__(self, word: object) -> bool:
        """Support ``word in trie``."""
        return isinstance(word, str) and self.contains(word)

    def starts_with(self, prefix: str) -> bool:
        """Return whether any stored term begins with ``prefix``.

        Args:
            prefix: The prefix to test; the empty prefix matches when the trie is non-empty.

        Returns:
            ``True`` when at least one term has this prefix.
        """
        if not prefix:
            return self._size > 0
        return self._find(prefix) is not None

    def score(self, word: str) -> float:
        """Return the score of a stored term.

        Args:
            word: The term to look up.

        Returns:
            Its score.

        Raises:
            KeyError: If ``word`` is not stored.
        """
        node = self._find(word)
        if node is None or not node.is_word:
            raise KeyError(word)
        return node.score

    def add_score(self, word: str, delta: float) -> float:
        """Increase the score of a stored term.

        Args:
            word: The term to update.
            delta: Amount added to its score.

        Returns:
            The new score.

        Raises:
            KeyError: If ``word`` is not stored.
        """
        node = self._find(word)
        if node is None or not node.is_word:
            raise KeyError(word)
        node.score += delta
        return node.score

    def delete(self, word: str) -> bool:
        """Remove ``word`` and prune nodes that no longer lead to any term.

        Args:
            word: The term to remove.

        Returns:
            ``True`` if the term was present and removed, ``False`` otherwise.
        """
        path: list[tuple[TrieNode, str]] = []
        node = self.root
        for char in word:
            child = node.children.get(char)
            if child is None:
                return False
            path.append((node, char))
            node = child
        if not node.is_word or not word:
            return False
        node.is_word = False
        node.score = 0.0
        self._size -= 1
        for parent, char in reversed(path):
            child = parent.children[char]
            if child.is_word or child.children:
                break
            del parent.children[char]
        return True

    def __len__(self) -> int:
        """Return the number of stored terms."""
        return self._size

    def _walk(self, node: TrieNode, prefix: str) -> Iterator[tuple[str, float]]:
        stack: list[tuple[TrieNode, str]] = [(node, prefix)]
        while stack:
            current, text = stack.pop()
            if current.is_word:
                yield text, current.score
            for char in sorted(current.children, reverse=True):
                stack.append((current.children[char], text + char))

    def items(self, prefix: str = "") -> Iterator[tuple[str, float]]:
        """Yield ``(term, score)`` pairs under ``prefix`` in lexicographic order.

        Args:
            prefix: Only terms starting with this prefix are yielded.

        Yields:
            Term and score pairs, sorted by term.
        """
        node = self._find(prefix)
        if node is not None:
            yield from self._walk(node, prefix)

    def words_with_prefix(self, prefix: str) -> list[str]:
        """Return every stored term that starts with ``prefix``, sorted.

        Args:
            prefix: The prefix to complete.

        Returns:
            Matching terms in lexicographic order.
        """
        return [word for word, _ in self.items(prefix)]

    def __iter__(self) -> Iterator[str]:
        """Iterate over all terms in lexicographic order."""
        return (word for word, _ in self.items())

    def top_k(self, prefix: str, k: int) -> list[tuple[str, float]]:
        """Return the ``k`` highest-scoring terms that start with ``prefix``.

        Ties on score are broken alphabetically. Uses a heap, so the cost is O(m log k) for m matches.

        Args:
            prefix: The prefix to complete.
            k: Maximum number of results.

        Returns:
            ``(term, score)`` pairs, best first.

        Raises:
            ValueError: If ``k`` is negative.
        """
        if k < 0:
            raise ValueError("k must be non-negative")
        if k == 0:
            return []
        return heapq.nsmallest(k, self.items(prefix), key=lambda pair: (-pair[1], pair[0]))
