"""Milestone 1: the Trie data structure."""

import pytest
from autocomplete import Trie


@pytest.fixture
def trie() -> Trie:
    t = Trie()
    for word in ["car", "card", "care", "cart", "cat", "dog", "do"]:
        t.insert(word)
    return t


def test_empty_trie_has_length_zero() -> None:
    t = Trie()
    assert len(t) == 0, "a new Trie should be empty"
    assert list(t) == [], "iterating an empty Trie should yield nothing"
    assert not t.starts_with(""), "the empty prefix matches nothing in an empty Trie"


def test_insert_and_contains(trie: Trie) -> None:
    assert trie.contains("card"), "inserted word 'card' should be found"
    assert "cat" in trie, "`in` should work via __contains__"
    assert not trie.contains("ca"), "'ca' is only a prefix, not a stored word"
    assert "cars" not in trie, "'cars' was never inserted"


def test_contains_non_string_is_false(trie: Trie) -> None:
    assert 42 not in trie, "non-strings are never members"


def test_len_counts_distinct_words(trie: Trie) -> None:
    assert len(trie) == 7, "seven distinct words were inserted"
    trie.insert("car")
    assert len(trie) == 7, "re-inserting an existing word must not change the length"


def test_insert_empty_word_raises() -> None:
    with pytest.raises(ValueError):
        Trie().insert("")


def test_starts_with(trie: Trie) -> None:
    assert trie.starts_with("ca"), "'ca' prefixes car, card, ..."
    assert trie.starts_with("dog"), "a full word is also a prefix of itself"
    assert not trie.starts_with("cb"), "no word starts with 'cb'"
    assert trie.starts_with(""), "the empty prefix matches a non-empty Trie"


def test_iteration_is_lexicographic(trie: Trie) -> None:
    assert list(trie) == ["car", "card", "care", "cart", "cat", "do", "dog"], "iterate words in sorted order"


def test_iteration_order_independent_of_insertion() -> None:
    words = ["zeta", "alpha", "mu", "al", "beta"]
    t = Trie()
    for word in words:
        t.insert(word)
    assert list(t) == sorted(words), "iteration order must not depend on insertion order"


def test_words_with_prefix(trie: Trie) -> None:
    assert trie.words_with_prefix("car") == ["car", "card", "care", "cart"], "all words under 'car', sorted"
    assert trie.words_with_prefix("x") == [], "unknown prefix gives an empty list"


def test_delete_leaf_word_prunes_branch(trie: Trie) -> None:
    assert trie.delete("cart") is True, "deleting a stored word returns True"
    assert "cart" not in trie
    assert not trie.starts_with("cart"), "the now-unused 'cart' branch should be pruned"
    assert "car" in trie, "deleting 'cart' must keep 'car'"
    assert len(trie) == 6


def test_delete_prefix_word_keeps_longer_words(trie: Trie) -> None:
    assert trie.delete("car") is True
    assert "car" not in trie, "'car' was deleted"
    assert trie.starts_with("car"), "'card' still uses the 'car' path"
    assert "card" in trie and "care" in trie


def test_delete_missing_word_returns_false(trie: Trie) -> None:
    assert trie.delete("ca") is False, "'ca' is a prefix, not a word"
    assert trie.delete("zebra") is False, "'zebra' was never inserted"
    assert trie.delete("") is False, "the empty string is never stored"
    assert len(trie) == 7, "failed deletes must not change the length"


def test_delete_everything_leaves_empty_trie(trie: Trie) -> None:
    for word in list(trie):
        trie.delete(word)
    assert len(trie) == 0
    assert trie.root.children == {}, "every node should be pruned once all words are gone"


def test_unicode_words() -> None:
    t = Trie()
    for word in ["café", "cafe", "日本", "日本語", "naïve"]:
        t.insert(word)
    assert "café" in t and "日本語" in t, "tries work on any Unicode characters"
    assert t.words_with_prefix("日本") == ["日本", "日本語"]
    assert t.words_with_prefix("caf") == ["cafe", "café"], "code-point order puts 'e' before 'é'"
