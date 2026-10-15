"""Autocomplete engine: a scored trie, an LRU cache, and typo-tolerant suggestions."""

from autocomplete.engine import AutocompleteEngine, EngineStats, normalize
from autocomplete.fuzzy import fuzzy_search, levenshtein, within_distance
from autocomplete.lru import LRUCache
from autocomplete.trie import Trie, TrieNode

__all__ = [
    "AutocompleteEngine",
    "EngineStats",
    "LRUCache",
    "Trie",
    "TrieNode",
    "fuzzy_search",
    "levenshtein",
    "normalize",
    "within_distance",
]
