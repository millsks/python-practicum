"""Analysis functions: counts, resolution times with uncertainty, trends, and a borough comparison."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class MedianEstimate:
    """A median with a bootstrap confidence interval.

    Attributes:
        median: Sample median.
        low: Lower bound of the interval.
        high: Upper bound of the interval.
        confidence: Confidence level, such as 0.95.
        n: Number of observations used.
    """

    median: float
    low: float
    high: float
    confidence: float
    n: int


@dataclass(frozen=True, slots=True)
class BoroughComparison:
    """Result of a two-sided Mann-Whitney U test on resolution hours.

    Attributes:
        borough_a: First borough.
        borough_b: Second borough.
        n_a: Closed requests in ``borough_a``.
        n_b: Closed requests in ``borough_b``.
        median_a: Median resolution hours in ``borough_a``.
        median_b: Median resolution hours in ``borough_b``.
        statistic: The U statistic for ``borough_a``.
        pvalue: Two-sided p-value.
    """

    borough_a: str
    borough_b: str
    n_a: int
    n_b: int
    median_a: float
    median_b: float
    statistic: float
    pvalue: float

    def significant(self, alpha: float = 0.05) -> bool:
        """Return whether ``pvalue < alpha``.

        Args:
            alpha: Significance level chosen before looking at the data.

        Returns:
            True when the difference is statistically significant at ``alpha``.
        """
        raise NotImplementedError


def requests_by(df: pd.DataFrame, column: str) -> pd.Series:
    """Count requests per value of ``column``, largest first (ties broken alphabetically).

    Args:
        df: Featured frame.
        column: Column to group by, such as ``"category"`` or ``"borough"``.

    Returns:
        Integer counts indexed by the column's values, named ``"requests"``.

    Raises:
        KeyError: If ``column`` is not in ``df``.
    """
    # TODO: df.groupby(column).size(), then order by (-count, label) and .rename("requests").
    raise NotImplementedError


def resolution_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize resolution hours per category with named aggregations.

    Args:
        df: Featured frame.

    Returns:
        One row per category (sorted by median, descending) with columns ``closed``, ``median_hours``,
        ``p90_hours``, and ``outliers``.
    """
    # TODO: keep rows with a resolution time, then groupby("category").agg(closed=("resolution_hours", "size"), ...).
    raise NotImplementedError


def bootstrap_median_ci(
    values: pd.Series | np.ndarray, *, n_boot: int = 2000, confidence: float = 0.95, seed: int = 0
) -> MedianEstimate:
    """Estimate a median and its percentile-bootstrap confidence interval.

    Missing values are dropped first. Each of ``n_boot`` resamples draws ``n`` values with replacement using
    ``numpy.random.default_rng(seed)``, so the result is deterministic.

    Args:
        values: Observations.
        n_boot: Number of bootstrap resamples.
        confidence: Interval confidence level in (0, 1).
        seed: Random seed.

    Returns:
        The median estimate.

    Raises:
        ValueError: If there are no non-missing values or ``confidence`` is not in (0, 1).
    """
    # TODO: rng.choice(data, size=(n_boot, data.size), replace=True); np.median(..., axis=1);
    # TODO: np.percentile(medians, [tail, 100 - tail]) where tail = (1 - confidence) / 2 * 100.
    raise NotImplementedError


def weekly_trend(df: pd.DataFrame, window: int = 4) -> pd.DataFrame:
    """Count requests per week (weeks start on Monday) with a trailing rolling mean.

    Args:
        df: Featured frame.
        window: Rolling window in weeks; the first ``window - 1`` weeks average what is available.

    Returns:
        A frame indexed by week start with integer column ``requests`` and float column ``rolling_mean``.
    """
    # TODO: df.set_index("created_at").resample("W-MON", label="left", closed="left").size()
    # TODO: .rolling(window, min_periods=1).mean()
    raise NotImplementedError


def compare_boroughs(df: pd.DataFrame, borough_a: str, borough_b: str) -> BoroughComparison:
    """Test whether resolution times differ between two boroughs.

    Uses the two-sided Mann-Whitney U test, which does not assume normality; resolution times are heavily
    right-skewed. Only closed requests with a known resolution time are used.

    Args:
        df: Featured frame.
        borough_a: First borough name.
        borough_b: Second borough name.

    Returns:
        The comparison.

    Raises:
        ValueError: If either borough has fewer than two closed requests.
    """
    # TODO: from scipy import stats; stats.mannwhitneyu(a, b, alternative="two-sided")
    raise NotImplementedError
