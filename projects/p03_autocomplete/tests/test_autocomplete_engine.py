"""Milestone 5: the engine facade."""

import random
import string
import time
from pathlib import Path

import pytest
from autocomplete import AutocompleteEngine, normalize


@pytest.fixture
def engine() -> AutocompleteEngine:
    e = AutocompleteEngine(cache_size=8, max_typos=1)
    for term, score in [("iPhone", 90), ("iPad", 70), ("iPod", 20), ("Kindle", 60), ("Keyboard", 40), ("Kettle", 40)]:
        e.add_term(term, score)
    return e


def test_normalize() -> None:
    assert normalize("  Hello   World ") == "hello world", "trim, collapse whitespace, lowercase"
    assert normalize("STRASSE") == normalize("Straße"), "casefold handles German sharp s"
    assert normalize("café") == normalize("café"), "combining accents are NFC-normalized"


def test_complete_is_case_insensitive(engine: AutocompleteEngine) -> None:
    assert engine.complete("IP", 3) == ["iphone", "ipad", "ipod"], "results are normalized and ranked by score"
    assert "IPHONE" in engine


def test_complete_ties_alphabetical(engine: AutocompleteEngine) -> None:
    assert engine.complete("ke", 5) == ["kettle", "keyboard"], "tie at 40 breaks alphabetically"


def test_complete_empty_prefix(engine: AutocompleteEngine) -> None:
    assert engine.complete("", 2) == ["iphone", "ipad"], "the empty prefix ranks the whole catalog"


def test_add_empty_term_raises(engine: AutocompleteEngine) -> None:
    with pytest.raises(ValueError):
        engine.add_term("   ")


def test_cache_hits_on_repeat(engine: AutocompleteEngine) -> None:
    engine.complete("i", 3)
    engine.complete("I", 3)
    stats = engine.stats()
    assert stats.cache_hits == 1 and stats.cache_misses == 1, "the second (normalized-identical) query hits the cache"
    assert stats.queries == 2
    assert stats.hit_rate == pytest.approx(0.5)


def test_cached_result_is_not_aliased(engine: AutocompleteEngine) -> None:
    first = engine.complete("i", 3)
    first.append("junk")
    assert engine.complete("i", 3) == ["iphone", "ipad", "ipod"], "mutating a returned list must not corrupt the cache"


def test_cache_invalidated_on_add(engine: AutocompleteEngine) -> None:
    engine.complete("i", 3)
    engine.add_term("iMac", 100)
    assert engine.complete("i", 3) == ["imac", "iphone", "ipad"], "adding a term must invalidate cached results"


def test_cache_invalidated_on_remove(engine: AutocompleteEngine) -> None:
    engine.complete("k", 3)
    assert engine.remove_term("KINDLE") is True
    assert engine.complete("k", 3) == ["kettle", "keyboard"]
    assert engine.remove_term("kindle") is False, "removing twice returns False"


def test_record_selection_boosts_and_reorders(engine: AutocompleteEngine) -> None:
    engine.complete("ip", 3)
    for _ in range(25):
        engine.record_selection("ipad")
    assert engine.score("iPad") == 95
    assert engine.complete("ip", 1) == ["ipad"], "selections boost a term above its rivals"
    assert engine.stats().selections == 25


def test_record_selection_unknown_raises(engine: AutocompleteEngine) -> None:
    with pytest.raises(KeyError):
        engine.record_selection("walkman")


def test_suggest_tops_up_with_typos(engine: AutocompleteEngine) -> None:
    assert engine.suggest("kettel", 3) == [], "two edits away is beyond max_typos=1"
    assert engine.suggest("ipda", 3) == [], "a transposition costs 2 in plain Levenshtein"
    assert engine.suggest("ipat", 3) == ["ipad"], "one substitution away"


def test_suggest_prefers_exact_prefix_matches(engine: AutocompleteEngine) -> None:
    result = engine.suggest("ipod", 3)
    assert result[0] == "ipod", "the exact completion comes first"
    assert result[1:] == ["ipad"], "then typo matches by distance, score, term"


def test_suggest_with_typos_disabled() -> None:
    e = AutocompleteEngine(max_typos=0)
    e.add_term("laptop", 5)
    assert e.suggest("labtop", 5) == []


def test_negative_max_typos_rejected() -> None:
    with pytest.raises(ValueError):
        AutocompleteEngine(max_typos=-1)


def test_load_csv(tmp_path: Path) -> None:
    path = tmp_path / "catalog.csv"
    path.write_text("term,score\nUSB Cable,12\nusb hub,30\n\nUSB  Cable,15\nMonitor,8.5\n", encoding="utf-8")
    e = AutocompleteEngine()
    assert e.load_csv(path) == 4, "four non-blank rows are loaded"
    assert len(e) == 3, "'USB Cable' and 'USB  Cable' normalize to the same term"
    assert e.score("usb cable") == 15, "a later row replaces the earlier score"
    assert e.complete("usb", 5) == ["usb hub", "usb cable"]


def test_load_csv_bad_score(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("term,score\nmouse,lots\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid score"):
        AutocompleteEngine().load_csv(path)


def test_load_csv_bad_header(tmp_path: Path) -> None:
    path = tmp_path / "header.csv"
    path.write_text("name,popularity\nmouse,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        AutocompleteEngine().load_csv(path)


def test_load_csv_invalidates_cache(tmp_path: Path, engine: AutocompleteEngine) -> None:
    engine.complete("k", 1)
    path = tmp_path / "more.csv"
    path.write_text("term,score\nkayak,500\n", encoding="utf-8")
    engine.load_csv(path)
    assert engine.complete("k", 1) == ["kayak"]


def test_unicode_catalog() -> None:
    e = AutocompleteEngine()
    e.add_term("Crème Brûlée", 3)
    e.add_term("Crêpe", 5)
    assert e.complete("CR", 5) == ["crêpe", "crème brûlée"]


def test_performance_20k_terms() -> None:
    rng = random.Random(3)
    e = AutocompleteEngine(cache_size=64)
    start = time.perf_counter()
    for i in range(20_000):
        term = "".join(rng.choices(string.ascii_lowercase, k=rng.randint(4, 10)))
        e.add_term(f"{term}{i}", rng.random() * 100)
    for prefix in ["a", "b", "ab", "cd", "x", "qu", "z"] * 3:
        assert len(e.complete(prefix, 10)) == 10
    elapsed = time.perf_counter() - start
    assert elapsed < 10.0, f"20k inserts + 21 top_k queries took {elapsed:.2f}s; aim for well under a few seconds"
