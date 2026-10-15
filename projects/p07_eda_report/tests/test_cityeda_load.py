"""Milestone 1: load the raw CSV with explicit dtypes."""

import pandas as pd
import pytest
from cityeda.generate import COLUMNS, write_requests
from cityeda.load import load_requests


@pytest.fixture(scope="module")
def raw(tmp_path_factory: pytest.TempPathFactory) -> pd.DataFrame:
    path = write_requests(tmp_path_factory.mktemp("load") / "requests.csv", 1000, seed=311)
    return load_requests(path)


def test_columns_in_order(raw: pd.DataFrame) -> None:
    assert tuple(raw.columns) == COLUMNS, "load_requests must return exactly COLUMNS, in order"


def test_row_count(raw: pd.DataFrame) -> None:
    assert len(raw) == 1020, "1000 requests plus 20 duplicates"


def test_text_columns_are_strings_not_dates(raw: pd.DataFrame) -> None:
    for column in ("request_id", "created_at", "closed_at", "category", "borough"):
        assert pd.api.types.is_string_dtype(raw[column]), f"{column} should load as text"
    assert not pd.api.types.is_datetime64_any_dtype(raw["created_at"]), "parse dates while cleaning, not loading"


def test_low_cardinality_columns_are_categorical(raw: pd.DataFrame) -> None:
    assert isinstance(raw["channel"].dtype, pd.CategoricalDtype), "channel should be a category dtype"
    assert isinstance(raw["status"].dtype, pd.CategoricalDtype), "status should be a category dtype"


def test_blank_fields_are_missing(raw: pd.DataFrame) -> None:
    distinct = raw.drop_duplicates("request_id")
    assert distinct["borough"].isna().sum() == 25, "the 25 blank boroughs should load as missing values"


def test_missing_column_is_an_error(tmp_path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("request_id,created_at\nSR-1,2025-01-06 10:00:00\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_requests(path)
