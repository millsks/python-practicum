"""Milestone 2: cleaning rules and the cleaning log."""

import pandas as pd
import pytest
from cityeda.clean import CleaningStep, clean_requests, normalize_borough, normalize_category
from cityeda.generate import mess_counts, write_requests
from cityeda.load import load_requests

N = 2000
CANONICAL = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island", "Unknown"}


@pytest.fixture(scope="module")
def raw(tmp_path_factory: pytest.TempPathFactory) -> pd.DataFrame:
    return load_requests(write_requests(tmp_path_factory.mktemp("clean") / "requests.csv", N, seed=311))


@pytest.fixture(scope="module")
def cleaned(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[CleaningStep]]:
    return clean_requests(raw)


def _affected(log: list[CleaningStep], rule: str) -> int:
    matches = [step.rows_affected for step in log if step.rule == rule]
    assert matches, f"the log has no step named {rule!r}"
    return matches[0]


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("Brooklyn", "Brooklyn"),
        ("  BROOKLYN ", "Brooklyn"),
        ("bklyn", "Brooklyn"),
        ("The Bronx", "Bronx"),
        ("BX", "Bronx"),
        ("New York", "Manhattan"),
        ("Staten  Island", "Staten Island"),
        ("si", "Staten Island"),
        ("Atlantis", "Unknown"),
        ("", "Unknown"),
        (None, "Unknown"),
        (float("nan"), "Unknown"),
    ],
)
def test_normalize_borough(raw_value: object, expected: str) -> None:
    assert normalize_borough(raw_value) == expected, f"normalize_borough({raw_value!r}) should be {expected!r}"


def test_normalize_category() -> None:
    assert normalize_category(" HEAT/HOT WATER ") == "Heat/Hot Water", "trim and title-case"
    assert normalize_category("street  light") == "Street Light", "collapse inner whitespace"
    assert normalize_category(None) is None, "missing stays missing"


def test_log_rules_in_order(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    rules = [step.rule for step in cleaned[1]]
    assert rules == [
        "drop_duplicate_ids",
        "normalize_category",
        "normalize_borough",
        "fill_missing_borough",
        "drop_invalid_created",
        "null_invalid_closed",
        "null_closed_before_created",
    ], "the cleaning log must list every rule in the documented order"


def test_log_entries_are_documented(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    for step in cleaned[1]:
        assert isinstance(step, CleaningStep), "log entries are CleaningStep objects"
        assert step.description.strip(), f"{step.rule} needs a human-readable description"
        assert step.rows_affected >= 0, "rows_affected cannot be negative"


def test_duplicates_removed(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    df, log = cleaned
    assert _affected(log, "drop_duplicate_ids") == mess_counts(N).duplicates, "one removal per injected duplicate"
    assert df["request_id"].is_unique, "request_id must be unique after cleaning"


def test_invalid_created_rows_dropped(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    df, log = cleaned
    assert _affected(log, "drop_invalid_created") == mess_counts(N).bad_created, "every bad created_at is dropped"
    assert len(df) == N - mess_counts(N).bad_created, "rows left = distinct requests minus bad created_at"
    assert df["created_at"].notna().all(), "no missing created_at after cleaning"


def test_dates_are_datetimes(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    df, _ = cleaned
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"]), "created_at must be datetime64"
    assert pd.api.types.is_datetime64_any_dtype(df["closed_at"]), "closed_at must be datetime64"


def test_invalid_closed_nulled(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    assert _affected(cleaned[1], "null_invalid_closed") == mess_counts(N).bad_closed, "'unknown' closed_at -> NaT"


def test_closed_before_created_nulled(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    df, log = cleaned
    assert _affected(log, "null_closed_before_created") == mess_counts(N).closed_before_created
    assert not (df["closed_at"] < df["created_at"]).any(), "no request may close before it opens"


def test_boroughs_canonical(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    df, log = cleaned
    assert set(df["borough"]) <= CANONICAL, f"unexpected boroughs: {set(df['borough']) - CANONICAL}"
    assert (df["borough"] == "Unknown").sum() == mess_counts(N).missing_borough, "only blanks become Unknown"
    assert _affected(log, "fill_missing_borough") == mess_counts(N).missing_borough


def test_categories_canonical(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    categories = set(cleaned[0]["category"])
    assert len(categories) == 7, f"expected 7 categories after normalizing, got {sorted(categories)}"
    assert all(c == c.strip() and c == c.title() for c in categories), "categories are trimmed and title-cased"


def test_sorted_with_fresh_index(cleaned: tuple[pd.DataFrame, list[CleaningStep]]) -> None:
    df, _ = cleaned
    assert df["created_at"].is_monotonic_increasing, "sort by created_at"
    assert list(df.index) == list(range(len(df))), "reset the index after sorting"


def test_input_not_modified(raw: pd.DataFrame) -> None:
    before = raw.copy()
    clean_requests(raw)
    pd.testing.assert_frame_equal(raw, before, obj="clean_requests must not change its input")
