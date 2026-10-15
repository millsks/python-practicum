"""Milestone 2: weighted completions with a heap."""

import pytest
from autocomplete import Trie


@pytest.fixture
def scored() -> Trie:
    t = Trie()
    for word, score in [
        ("apple", 50),
        ("app", 80),
        ("application", 80),
        ("apply", 10),
        ("apricot", 30),
        ("banana", 99),
    ]:
        t.insert(word, score)
    return t


def test_score_lookup(scored: Trie) -> None:
    assert scored.score("apple") == 50
    with pytest.raises(KeyError):
        scored.score("ap")


def test_insert_existing_updates_score(scored: Trie) -> None:
    scored.insert("apply", 95)
    assert scored.score("apply") == 95, "inserting an existing word replaces its score"
    assert len(scored) == 6


def test_add_score(scored: Trie) -> None:
    assert scored.add_score("apricot", 5) == 35, "add_score returns the new score"
    with pytest.raises(KeyError):
        scored.add_score("missing", 1)


def test_top_k_orders_by_score_then_alpha(scored: Trie) -> None:
    result = scored.top_k("ap", 4)
    assert result == [("app", 80), ("application", 80), ("apple", 50), ("apricot", 30)], (
        "highest score first; the tie at 80 is broken alphabetically"
    )


def test_top_k_fewer_matches_than_k(scored: Trie) -> None:
    assert scored.top_k("appl", 10) == [("application", 80), ("apple", 50), ("apply", 10)]


def test_top_k_empty_prefix_ranks_everything(scored: Trie) -> None:
    assert scored.top_k("", 2) == [("banana", 99), ("app", 80)], "the empty prefix matches every word"


def test_top_k_unknown_prefix_and_zero_k(scored: Trie) -> None:
    assert scored.top_k("zz", 3) == [], "no matches gives an empty list"
    assert scored.top_k("ap", 0) == [], "k=0 gives an empty list"


def test_top_k_negative_k_raises(scored: Trie) -> None:
    with pytest.raises(ValueError):
        scored.top_k("ap", -1)


def test_top_k_all_ties_are_alphabetical() -> None:
    t = Trie()
    for word in ["delta", "alpha", "charlie", "bravo"]:
        t.insert(word, 1)
    assert [w for w, _ in t.top_k("", 3)] == ["alpha", "bravo", "charlie"]


def test_items_yields_scores(scored: Trie) -> None:
    assert list(scored.items("appl")) == [("apple", 50), ("application", 80), ("apply", 10)]
