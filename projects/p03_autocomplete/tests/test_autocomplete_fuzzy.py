"""Milestone 4: typo tolerance with a bounded Levenshtein search."""

import pytest
from autocomplete import Trie, fuzzy_search, levenshtein, within_distance


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [("", "", 0), ("abc", "", 3), ("kitten", "sitting", 3), ("flaw", "lawn", 2), ("same", "same", 0), ("ab", "ba", 2)],
)
def test_levenshtein(a: str, b: str, expected: int) -> None:
    assert levenshtein(a, b) == expected, f"levenshtein({a!r}, {b!r}) should be {expected}"


def test_levenshtein_is_symmetric() -> None:
    assert levenshtein("sunday", "saturday") == levenshtein("saturday", "sunday") == 3


def test_within_distance() -> None:
    assert within_distance("kitten", "sitting", 3)
    assert not within_distance("kitten", "sitting", 2)
    assert not within_distance("a", "abcdef", 2), "a length gap larger than the bound fails fast"


@pytest.fixture
def words() -> Trie:
    t = Trie()
    for word in ["laptop", "laptops", "lapdog", "tablet", "table", "cable", "label"]:
        t.insert(word, 1)
    return t


def test_fuzzy_exact_match_distance_zero(words: Trie) -> None:
    assert fuzzy_search(words, "table", 0) == [("table", 0)]


def test_fuzzy_one_typo(words: Trie) -> None:
    assert fuzzy_search(words, "labtop", 1) == [("laptop", 1)], "one substitution away"


def test_fuzzy_sorted_by_distance_then_term(words: Trie) -> None:
    assert fuzzy_search(words, "tabel", 2) == [("label", 1), ("table", 2), ("tablet", 2)]


def test_fuzzy_matches_brute_force(words: Trie) -> None:
    for query in ["lapto", "cabel", "xyz", "tablets", "l"]:
        for limit in (1, 2):
            expected = sorted(
                ((w, levenshtein(query, w)) for w in words if levenshtein(query, w) <= limit),
                key=lambda pair: (pair[1], pair[0]),
            )
            assert fuzzy_search(words, query, limit) == expected, f"query={query!r} limit={limit}"


def test_fuzzy_negative_distance_raises(words: Trie) -> None:
    with pytest.raises(ValueError):
        fuzzy_search(words, "x", -1)
