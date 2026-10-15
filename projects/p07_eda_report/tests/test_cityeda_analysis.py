"""Milestone 4: analysis functions on a fixed-seed dataset."""

import numpy as np
import pandas as pd
import pytest
from cityeda.analysis import (
    BoroughComparison,
    MedianEstimate,
    bootstrap_median_ci,
    compare_boroughs,
    requests_by,
    resolution_summary,
    weekly_trend,
)
from cityeda.clean import clean_requests
from cityeda.features import add_features
from cityeda.generate import write_requests
from cityeda.load import load_requests
from scipy import stats


@pytest.fixture(scope="module")
def df(tmp_path_factory: pytest.TempPathFactory) -> pd.DataFrame:
    path = write_requests(tmp_path_factory.mktemp("analysis") / "requests.csv", 2000, seed=311)
    return add_features(clean_requests(load_requests(path))[0])


def test_requests_by_category(df: pd.DataFrame) -> None:
    counts = requests_by(df, "category")
    assert counts.sum() == len(df) == 1980, "every cleaned row is counted once"
    assert counts.index[0] == "Noise" and counts.iloc[0] == 503, "Noise is the top category with 503 requests"
    assert counts.is_monotonic_decreasing, "largest first"
    assert counts.name == "requests", "name the series 'requests'"


def test_requests_by_borough(df: pd.DataFrame) -> None:
    counts = requests_by(df, "borough")
    assert counts.to_dict() == {
        "Brooklyn": 554,
        "Queens": 531,
        "Bronx": 366,
        "Manhattan": 362,
        "Staten Island": 117,
        "Unknown": 50,
    }, "borough counts on the seed-311 dataset"


def test_requests_by_breaks_ties_alphabetically() -> None:
    frame = pd.DataFrame({"k": ["b", "a", "c", "c"]})
    assert list(requests_by(frame, "k").index) == ["c", "a", "b"], "ties are ordered alphabetically"


def test_requests_by_unknown_column(df: pd.DataFrame) -> None:
    with pytest.raises(KeyError):
        requests_by(df, "no_such_column")


def test_resolution_summary(df: pd.DataFrame) -> None:
    summary = resolution_summary(df)
    assert list(summary.columns) == ["closed", "median_hours", "p90_hours", "outliers"], "named aggregation columns"
    assert summary["median_hours"].is_monotonic_decreasing, "slowest category first"
    noise = df.loc[(df["category"] == "Noise") & df["resolution_hours"].notna(), "resolution_hours"]
    assert summary.loc["Noise", "closed"] == len(noise), "closed counts only resolved requests"
    assert summary.loc["Noise", "median_hours"] == pytest.approx(noise.median()), "median per category"
    assert summary["outliers"].sum() == df["is_outlier"].sum(), "outlier counts add up"


def test_bootstrap_median_fixed_seed(df: pd.DataFrame) -> None:
    est = bootstrap_median_ci(df["resolution_hours"], seed=0)
    assert isinstance(est, MedianEstimate), "return a MedianEstimate"
    assert est.n == int(df["resolution_hours"].notna().sum()) == 1806, "NaN values are dropped"
    assert est.median == pytest.approx(df["resolution_hours"].median()), "median of the observed data"
    assert est.low < est.median < est.high, "the interval brackets the median"
    assert est.median == pytest.approx(25.2, abs=0.05), "median resolution on seed 311 is about 25.2 hours"


def test_bootstrap_is_deterministic() -> None:
    values = np.arange(1.0, 101.0)
    assert bootstrap_median_ci(values, seed=3) == bootstrap_median_ci(values, seed=3), "same seed, same interval"


def test_bootstrap_wider_at_higher_confidence() -> None:
    values = np.random.default_rng(1).exponential(10, size=300)
    narrow = bootstrap_median_ci(values, confidence=0.8, seed=1)
    wide = bootstrap_median_ci(values, confidence=0.99, seed=1)
    assert wide.high - wide.low > narrow.high - narrow.low, "99% intervals are wider than 80% intervals"


def test_bootstrap_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        bootstrap_median_ci([1.0, 2.0], confidence=1.5)
    with pytest.raises(ValueError):
        bootstrap_median_ci(pd.Series([np.nan, np.nan]))


def test_weekly_trend(df: pd.DataFrame) -> None:
    trend = weekly_trend(df, window=4)
    assert list(trend.columns) == ["requests", "rolling_mean"], "two columns: requests and rolling_mean"
    assert len(trend) == 26, "the data covers 26 weeks"
    assert trend["requests"].sum() == len(df), "every request lands in one week"
    assert (trend.index.weekday == 0).all(), "weeks are labelled by their Monday"
    assert trend.index[0] == pd.Timestamp("2025-01-06"), "first week starts 2025-01-06"
    assert trend["rolling_mean"].iloc[0] == trend["requests"].iloc[0], "min_periods=1: first mean is the first count"
    assert trend["rolling_mean"].iloc[5] == pytest.approx(trend["requests"].iloc[2:6].mean()), "4-week trailing mean"


def test_compare_boroughs_matches_scipy(df: pd.DataFrame) -> None:
    result = compare_boroughs(df, "Bronx", "Manhattan")
    a = df.loc[df["borough"] == "Bronx", "resolution_hours"].dropna()
    b = df.loc[df["borough"] == "Manhattan", "resolution_hours"].dropna()
    expected = stats.mannwhitneyu(a, b, alternative="two-sided")
    assert isinstance(result, BoroughComparison), "return a BoroughComparison"
    assert (result.n_a, result.n_b) == (len(a), len(b)) == (338, 328), "closed requests per borough"
    assert result.statistic == pytest.approx(expected.statistic), "U statistic from scipy.stats.mannwhitneyu"
    assert result.pvalue == pytest.approx(expected.pvalue), "two-sided p-value"


def test_bronx_is_slower(df: pd.DataFrame) -> None:
    result = compare_boroughs(df, "Bronx", "Manhattan")
    assert result.median_a > result.median_b, "the Bronx resolves requests more slowly in this dataset"
    assert result.significant(0.05), "the difference is significant at alpha = 0.05"
    assert not result.significant(1e-9), "but not at an absurdly strict alpha"


def test_compare_boroughs_needs_data(df: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        compare_boroughs(df, "Bronx", "Atlantis")
