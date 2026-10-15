"""Milestone 0: the provided synthetic data generator (these pass from the start)."""

import csv
import io

import pytest
from cityeda.generate import COLUMNS, generate_requests, mess_counts, write_requests


def _rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def test_same_seed_is_byte_identical() -> None:
    assert generate_requests(500, seed=7) == generate_requests(500, seed=7), "same (n, seed) must give the same CSV"


def test_different_seeds_differ() -> None:
    assert generate_requests(500, seed=7) != generate_requests(500, seed=8), "different seeds should give new data"


def test_header_and_row_count() -> None:
    text = generate_requests(1000, seed=1)
    assert tuple(text.splitlines()[0].split(",")) == COLUMNS, "header must list COLUMNS in order"
    assert len(_rows(text)) == 1000 + mess_counts(1000).duplicates, "n rows plus the injected duplicates"


def test_duplicate_ids_are_injected() -> None:
    rows = _rows(generate_requests(1000, seed=1))
    ids = [r["request_id"] for r in rows]
    assert len(ids) - len(set(ids)) == mess_counts(1000).duplicates, "exactly n // 50 repeated IDs"


def test_borough_spellings_are_messy() -> None:
    boroughs = {r["borough"] for r in _rows(generate_requests(1000, seed=1))}
    assert {"Brooklyn", "BROOKLYN", "Bklyn", ""} <= boroughs, "raw boroughs mix casing, aliases, and blanks"


def test_small_n_rejected() -> None:
    with pytest.raises(ValueError):
        generate_requests(50)


def test_write_requests_creates_parents(tmp_path) -> None:
    path = write_requests(tmp_path / "raw" / "requests.csv", 300, seed=2)
    assert path.read_text(encoding="utf-8") == generate_requests(300, seed=2), "file holds the generated CSV"
