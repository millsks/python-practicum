"""Milestone 3: feature engineering."""

import numpy as np
import pandas as pd
import pytest
from cityeda.clean import clean_requests
from cityeda.features import WEEKDAYS, add_features, iqr_outliers
from cityeda.generate import mess_counts, write_requests
from cityeda.load import load_requests


@pytest.fixture(scope="module")
def featured(tmp_path_factory: pytest.TempPathFactory) -> pd.DataFrame:
    path = write_requests(tmp_path_factory.mktemp("features") / "requests.csv", 2000, seed=311)
    return add_features(clean_requests(load_requests(path))[0])


def test_resolution_hours(featured: pd.DataFrame) -> None:
    expected = (featured["closed_at"] - featured["created_at"]).dt.total_seconds() / 3600
    np.testing.assert_allclose(featured["resolution_hours"], expected, err_msg="hours from created_at to closed_at")
    assert featured.loc[featured["closed_at"].isna(), "resolution_hours"].isna().all(), "open requests have NaN"
    assert (featured["resolution_hours"].dropna() >= 0).all(), "no negative durations survive cleaning"


def test_weekday_is_ordered_category(featured: pd.DataFrame) -> None:
    dtype = featured["weekday"].dtype
    assert isinstance(dtype, pd.CategoricalDtype) and dtype.ordered, "weekday is an ordered categorical"
    assert list(dtype.categories) == list(WEEKDAYS), "categories run Monday..Sunday"
    assert (featured["weekday"].astype(str) == featured["created_at"].dt.day_name()).all()


def test_hour(featured: pd.DataFrame) -> None:
    assert featured["hour"].between(0, 23).all(), "hour is 0-23"
    assert (featured["hour"] == featured["created_at"].dt.hour).all(), "hour comes from created_at"


def test_week_starts_on_monday(featured: pd.DataFrame) -> None:
    assert (featured["week"].dt.weekday == 0).all(), "week is the Monday of the request's week"
    assert (featured["week"] <= featured["created_at"]).all(), "week start is on or before created_at"
    assert ((featured["created_at"] - featured["week"]) < pd.Timedelta(days=7)).all(), "within 7 days"


def test_injected_outliers_flagged(featured: pd.DataFrame) -> None:
    extreme = featured["resolution_hours"] > 1500
    assert extreme.sum() >= mess_counts(2000).outliers, "the injected extreme durations survive cleaning"
    assert featured.loc[extreme, "is_outlier"].all(), "every >1500-hour request must be flagged"
    assert featured["is_outlier"].mean() < 0.05, "k=3 within each category flags only a few percent"


def test_iqr_outliers_simple_case() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 100.0, np.nan])
    flags = iqr_outliers(values, k=1.5)
    assert flags.tolist() == [False, False, False, False, False, True, False], "only 100 is outside the fences"


def test_add_features_does_not_mutate(tmp_path) -> None:
    path = write_requests(tmp_path / "r.csv", 300, seed=5)
    cleaned, _ = clean_requests(load_requests(path))
    columns = list(cleaned.columns)
    add_features(cleaned)
    assert list(cleaned.columns) == columns, "add_features returns a new frame"
