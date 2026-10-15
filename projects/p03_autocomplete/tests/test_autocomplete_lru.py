"""Milestone 3: an LRU cache built from scratch."""

import inspect

import autocomplete.lru
import pytest
from autocomplete import LRUCache


def test_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        LRUCache(0)


def test_put_and_get() -> None:
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1
    assert cache.get("missing") is None, "a miss returns the default (None)"
    assert cache.get("missing", -1) == -1, "a miss returns the given default"
    assert cache.capacity == 2


def test_evicts_least_recently_used() -> None:
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert "b" not in cache, "'b' was least recently used and should be evicted"
    assert "a" in cache and "c" in cache
    assert len(cache) == 2


def test_put_existing_refreshes_without_growing() -> None:
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    cache.put("c", 3)
    assert cache.get("a") == 10, "updating 'a' refreshes its recency and value"
    assert "b" not in cache


def test_keys_most_recent_first() -> None:
    cache: LRUCache[int, str] = LRUCache(3)
    for key in (1, 2, 3):
        cache.put(key, str(key))
    cache.get(1)
    assert cache.keys() == [1, 3, 2], "keys() lists most to least recently used"


def test_contains_does_not_change_recency() -> None:
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache
    cache.put("c", 3)
    assert "a" not in cache, "`in` must not count as a use"


def test_hit_and_miss_counters() -> None:
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    cache.get("zzz")
    assert (cache.hits, cache.misses) == (2, 1)


def test_clear() -> None:
    cache: LRUCache[str, int] = LRUCache(2)
    cache.put("a", 1)
    cache.clear()
    assert len(cache) == 0 and cache.keys() == []
    cache.put("b", 2)
    assert cache.get("b") == 2, "the cache keeps working after clear()"


def test_capacity_one() -> None:
    cache: LRUCache[str, int] = LRUCache(1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.keys() == ["b"]


def test_no_ordereddict() -> None:
    source = inspect.getsource(autocomplete.lru)
    assert "OrderedDict" not in source, "build the cache from a dict plus a doubly linked list, not OrderedDict"
    assert "lru_cache" not in source, "do not wrap functools.lru_cache"
