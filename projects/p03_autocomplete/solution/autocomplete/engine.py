"""The autocomplete engine facade: normalization, caching, typo tolerance, CSV loading, and stats."""

import csv
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from autocomplete.fuzzy import fuzzy_search
from autocomplete.lru import LRUCache
from autocomplete.trie import Trie


def normalize(text: str) -> str:
    """Return the canonical form used for storing and matching terms.

    Applies Unicode NFC normalization, trims surrounding whitespace, collapses internal runs of
    whitespace to one space, and case-folds (so ``"Straße"`` matches ``"STRASSE"``).

    Args:
        text: Raw user or catalog text.

    Returns:
        The normalized text.
    """
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


@dataclass(frozen=True, slots=True)
class EngineStats:
    """A snapshot of engine activity.

    Attributes:
        terms: Number of stored terms.
        queries: Number of ``complete``/``suggest`` calls.
        cache_hits: Completions answered from the cache.
        cache_misses: Completions computed from the trie.
        selections: Number of recorded selections.
    """

    terms: int
    queries: int
    cache_hits: int
    cache_misses: int
    selections: int

    @property
    def hit_rate(self) -> float:
        """Fraction of cache lookups that hit, or 0.0 before any lookup."""
        lookups = self.cache_hits + self.cache_misses
        return self.cache_hits / lookups if lookups else 0.0


class AutocompleteEngine:
    """Search-box autocomplete over a catalog of scored terms."""

    def __init__(self, *, cache_size: int = 256, max_typos: int = 1, selection_boost: float = 1.0) -> None:
        """Create an empty engine.

        Args:
            cache_size: Capacity of the completion cache.
            max_typos: Largest edit distance ``suggest`` tolerates (0 disables typo tolerance).
            selection_boost: Score added each time a term is selected.

        Raises:
            ValueError: If ``max_typos`` is negative or ``cache_size`` is less than 1.
        """
        if max_typos < 0:
            raise ValueError("max_typos must be non-negative")
        self._trie = Trie()
        self._cache: LRUCache[tuple[str, int], list[str]] = LRUCache(cache_size)
        self.max_typos = max_typos
        self.selection_boost = selection_boost
        self._queries = 0
        self._selections = 0

    def __len__(self) -> int:
        """Return the number of stored terms."""
        return len(self._trie)

    def __contains__(self, term: object) -> bool:
        """Return whether ``term`` (after normalization) is stored."""
        return isinstance(term, str) and normalize(term) in self._trie

    def add_term(self, term: str, score: float = 1.0) -> None:
        """Add a term or replace its score.

        Args:
            term: The catalog term.
            score: Its popularity score.

        Raises:
            ValueError: If the term is empty after normalization.
        """
        key = normalize(term)
        if not key:
            raise ValueError("term is empty after normalization")
        self._trie.insert(key, score)
        self._cache.clear()

    def remove_term(self, term: str) -> bool:
        """Remove a term.

        Args:
            term: The term to remove.

        Returns:
            ``True`` if it was present.
        """
        removed = self._trie.delete(normalize(term))
        if removed:
            self._cache.clear()
        return removed

    def score(self, term: str) -> float:
        """Return a term's current score.

        Args:
            term: The term to look up.

        Returns:
            Its score.

        Raises:
            KeyError: If the term is not stored.
        """
        return self._trie.score(normalize(term))

    def load_csv(self, path: Path) -> int:
        """Load terms from a CSV file with a ``term,score`` header.

        Blank rows are skipped; a later row for the same term replaces the earlier score.

        Args:
            path: The CSV file.

        Returns:
            The number of rows loaded.

        Raises:
            ValueError: If the header is wrong or a row has a missing term or a non-numeric score.
        """
        loaded = 0
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or not {"term", "score"} <= set(reader.fieldnames):
                raise ValueError(f"{path}: expected a header with 'term' and 'score' columns")
            for row in reader:
                term = (row.get("term") or "").strip()
                raw_score = (row.get("score") or "").strip()
                if not term and not raw_score:
                    continue
                if not term:
                    raise ValueError(f"{path}:{reader.line_num}: missing term")
                try:
                    score = float(raw_score)
                except ValueError as exc:
                    raise ValueError(f"{path}:{reader.line_num}: invalid score {raw_score!r}") from exc
                self._trie.insert(normalize(term), score)
                loaded += 1
        self._cache.clear()
        return loaded

    def complete(self, prefix: str, k: int = 10) -> list[str]:
        """Return up to ``k`` terms starting with ``prefix``, most popular first.

        Results are cached; the cache is cleared whenever terms or scores change.

        Args:
            prefix: What the user has typed so far.
            k: Maximum number of results.

        Returns:
            Matching terms ordered by score (descending), then alphabetically.
        """
        self._queries += 1
        return self._complete(normalize(prefix), k)

    def _complete(self, key: str, k: int) -> list[str]:
        cached = self._cache.get((key, k))
        if cached is not None:
            return list(cached)
        result = [term for term, _ in self._trie.top_k(key, k)]
        self._cache.put((key, k), result)
        return list(result)

    def suggest(self, query: str, k: int = 10) -> list[str]:
        """Return completions, topped up with typo-tolerant matches when there are fewer than ``k``.

        Exact-prefix completions come first. Remaining slots are filled with terms within
        ``max_typos`` edits of the query, ordered by distance, then score (descending), then term.

        Args:
            query: What the user has typed.
            k: Maximum number of results.

        Returns:
            Suggested terms without duplicates.
        """
        self._queries += 1
        key = normalize(query)
        results = self._complete(key, k)
        if len(results) >= k or self.max_typos == 0 or not key:
            return results
        seen = set(results)
        matches = [(term, dist) for term, dist in fuzzy_search(self._trie, key, self.max_typos) if term not in seen]
        matches.sort(key=lambda pair: (pair[1], -self._trie.score(pair[0]), pair[0]))
        results.extend(term for term, _ in matches[: k - len(results)])
        return results

    def record_selection(self, term: str) -> float:
        """Record that the user picked ``term``, boosting its score.

        Args:
            term: The selected term.

        Returns:
            The term's new score.

        Raises:
            KeyError: If the term is not stored.
        """
        new_score = self._trie.add_score(normalize(term), self.selection_boost)
        self._selections += 1
        self._cache.clear()
        return new_score

    def stats(self) -> EngineStats:
        """Return a snapshot of engine activity."""
        return EngineStats(
            terms=len(self._trie),
            queries=self._queries,
            cache_hits=self._cache.hits,
            cache_misses=self._cache.misses,
            selections=self._selections,
        )
