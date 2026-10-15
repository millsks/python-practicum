"""A prefix tree (trie) that stores terms with popularity scores."""

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
        # TODO(milestone 1): walk from self.root, creating a TrieNode per missing character
        # (dict.setdefault is handy). Mark the last node as a word, bump self._size only if it is new,
        # and store the score.
        raise NotImplementedError

    def contains(self, word: str) -> bool:
        """Return whether ``word`` is a stored term (not merely a prefix).

        Args:
            word: The term to look up.

        Returns:
            ``True`` when the term was inserted and not deleted.
        """
        # TODO(milestone 1): write a private helper `_find(prefix) -> TrieNode | None` and reuse it here,
        # in starts_with, score, add_score, and items.
        raise NotImplementedError

    def __contains__(self, word: object) -> bool:
        """Support ``word in trie``."""
        # TODO(milestone 1): non-strings are never members; otherwise delegate to contains().
        raise NotImplementedError

    def starts_with(self, prefix: str) -> bool:
        """Return whether any stored term begins with ``prefix``.

        Args:
            prefix: The prefix to test; the empty prefix matches when the trie is non-empty.

        Returns:
            ``True`` when at least one term has this prefix.
        """
        # TODO(milestone 1): a prefix exists if its node exists, because delete() prunes dead branches.
        raise NotImplementedError

    def score(self, word: str) -> float:
        """Return the score of a stored term.

        Args:
            word: The term to look up.

        Returns:
            Its score.

        Raises:
            KeyError: If ``word`` is not stored.
        """
        # TODO(milestone 2)
        raise NotImplementedError

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
        # TODO(milestone 2)
        raise NotImplementedError

    def delete(self, word: str) -> bool:
        """Remove ``word`` and prune nodes that no longer lead to any term.

        Args:
            word: The term to remove.

        Returns:
            ``True`` if the term was present and removed, ``False`` otherwise.
        """
        # TODO(milestone 1): record the (parent, char) path while walking down. Unmark the word, then walk
        # the path backwards deleting children that are neither words nor have children of their own.
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of stored terms."""
        # TODO(milestone 1)
        raise NotImplementedError

    def items(self, prefix: str = "") -> Iterator[tuple[str, float]]:
        """Yield ``(term, score)`` pairs under ``prefix`` in lexicographic order.

        Args:
            prefix: Only terms starting with this prefix are yielded.

        Yields:
            Term and score pairs, sorted by term.
        """
        # TODO(milestone 1): depth-first walk from the prefix node. Visit children in sorted key order and
        # yield a node's own word before its descendants ("car" comes before "card").
        raise NotImplementedError

    def words_with_prefix(self, prefix: str) -> list[str]:
        """Return every stored term that starts with ``prefix``, sorted.

        Args:
            prefix: The prefix to complete.

        Returns:
            Matching terms in lexicographic order.
        """
        # TODO(milestone 1): build on items().
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        """Iterate over all terms in lexicographic order."""
        # TODO(milestone 1): build on items().
        raise NotImplementedError

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
        # TODO(milestone 2): use heapq. The sort key (-score, term) puts the highest score first and breaks
        # ties alphabetically; heapq.nsmallest(k, iterable, key=...) or a bounded heap of size k both work.
        raise NotImplementedError
