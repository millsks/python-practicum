# Project 3: Autocomplete Engine

Closes Part 3 (Data Structures). Full brief with diagrams and hints: `docs/projects/p03-autocomplete.html`.

## Scenario

You are building the search box for an online electronics store. As the shopper types, the box must show the ten
most popular matching products within a few milliseconds, survive typos ("labtop"), and learn from what people
click. You will build it from first principles: a trie, a heap-based ranker, an LRU cache, and a pruned
edit-distance search, joined behind one engine facade.

## Start and grade

```bash
pixi run start p03          # copies the starter into work/p03_autocomplete/
pixi run grade p03          # runs the tests against your work/ copy
```

## Package layout (`autocomplete`)

| Module | Contents |
|---|---|
| `trie.py` | `TrieNode`, `Trie` (insert, contains, starts_with, delete, `__len__`, sorted iteration, scores, `top_k`) |
| `lru.py` | `LRUCache[K, V]` built from a dict plus a doubly linked list with sentinels |
| `fuzzy.py` | `levenshtein`, `within_distance`, `fuzzy_search` (Levenshtein rows computed while walking the trie) |
| `engine.py` | `normalize`, `EngineStats`, `AutocompleteEngine` (CSV loading, caching, selections, suggestions, stats) |

## Milestones

1. **Trie** (`test_autocomplete_trie.py`): insert, membership, prefix test, delete with pruning, length, and
   lexicographic iteration. Works for any Unicode text.
2. **Weighted completions** (`test_autocomplete_ranking.py`): each term has a score; `top_k(prefix, k)` uses
   `heapq` and returns the best k, ties broken alphabetically.
3. **LRU cache** (`test_autocomplete_lru.py`): O(1) `get`/`put`, eviction of the least recently used entry,
   hit/miss counters. No `OrderedDict`, no `functools.lru_cache`.
4. **Typo tolerance** (`test_autocomplete_fuzzy.py`): Levenshtein distance and a trie search that prunes a branch
   as soon as every entry in its DP row exceeds the bound.
5. **Engine facade** (`test_autocomplete_engine.py`): normalization (NFC + casefold + whitespace), CSV loading,
   cached completions invalidated on every update, selection boosts, typo top-up, stats, and a 20k-term
   performance sanity check.

## Requirements

- Full type hints and Google-style docstrings; `pixi run ruff check work/p03_autocomplete` should be clean.
- Library code returns values; it never prints.
- Returned lists must be copies: callers may mutate them without corrupting the cache.

## Stretch goals

- Fuzzy *prefix* matching: suggest "laptop" while the user has typed only "labt".
- Damerau-Levenshtein, so that a transposition ("ipda") costs 1.
- Store the top-k at each trie node for O(L) queries, and keep them correct on updates.
- Invalidate only the cache entries whose prefix is a prefix of the changed term.
- A tiny CLI (`pixi run python -m autocomplete catalog.csv`) with an interactive prompt.
