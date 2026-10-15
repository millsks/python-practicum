"""Milestone 2: word ladders with BFS and bidirectional BFS."""

import itertools

import pytest
from puzzles import word_ladder

WORDS = ["hot", "dot", "dog", "lot", "log", "cog"]
FOUR = ["cold", "cord", "card", "ward", "warm", "word", "worm", "corm", "wore", "core", "bold", "bolt"]


def is_ladder(path: list[str], words: set[str]) -> bool:
    steps_ok = all(sum(a != b for a, b in zip(x, y, strict=True)) == 1 for x, y in itertools.pairwise(path))
    return steps_ok and all(w in words for w in path[1:])


def test_neighbors() -> None:
    assert word_ladder.neighbors("hot", set(WORDS)) == ["dot", "lot"], "neighbors differ in one letter, sorted"
    assert word_ladder.neighbors("xyz", set(WORDS)) == [], "no neighbors gives an empty list"


@pytest.mark.parametrize("bidirectional", [False, True])
def test_classic_ladder(bidirectional: bool) -> None:
    path = word_ladder.ladder("hit", "cog", WORDS, bidirectional=bidirectional)
    assert path is not None and len(path) == 5, "hit -> hot -> dot/lot -> dog/log -> cog has 5 words"
    assert path[0] == "hit" and path[-1] == "cog", "the ladder starts and ends at the given words"
    assert is_ladder(path, set(WORDS)), "every step must change exactly one letter and use dictionary words"


@pytest.mark.parametrize("bidirectional", [False, True])
def test_four_letter_ladder(bidirectional: bool) -> None:
    path = word_ladder.ladder("cold", "warm", FOUR, bidirectional=bidirectional)
    assert path is not None and len(path) == 5, "cold -> cord -> card -> ward -> warm (or equal length) is shortest"
    assert is_ladder(path, set(FOUR)), "the ladder must be valid"


@pytest.mark.parametrize("bidirectional", [False, True])
def test_no_ladder(bidirectional: bool) -> None:
    assert word_ladder.ladder("hit", "cog", ["hot", "dot", "lot"], bidirectional=bidirectional) is None, (
        "the end word missing from the dictionary means no ladder"
    )
    assert word_ladder.ladder("cold", "bolt", ["cold", "bolt", "warm"], bidirectional=bidirectional) is None, (
        "disconnected words have no ladder"
    )


def test_same_word_and_length_mismatch() -> None:
    assert word_ladder.ladder("cog", "cog", WORDS) == ["cog"], "start == end is a one-word ladder"
    assert word_ladder.ladder("hit", "cogs", [*WORDS, "cogs"]) is None, "words of different lengths never connect"


def test_case_insensitive() -> None:
    path = word_ladder.ladder("HIT", "Cog", [w.upper() for w in WORDS])
    assert path is not None and path[0] == "hit" and path[-1] == "cog", "comparison is case-insensitive, lowercase out"


def test_bidirectional_matches_bfs_length_on_chain() -> None:
    chain = ["aaaa", "baaa", "bbaa", "bbba", "bbbb", "cbbb", "ccbb", "cccb", "cccc", "abaa", "acaa"]
    plain = word_ladder.ladder("aaaa", "cccc", chain)
    both = word_ladder.ladder("aaaa", "cccc", chain, bidirectional=True)
    assert plain is not None and both is not None, "a chain of one-letter changes connects aaaa to cccc"
    assert len(plain) == len(both) == 9, "both searches must find the optimal 9-word ladder"
    assert is_ladder(both, set(chain)), "bidirectional paths must be valid ladders"
