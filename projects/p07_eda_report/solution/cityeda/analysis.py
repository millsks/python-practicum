"""Analysis functions: counts, resolution times with uncertainty, trends, and a borough comparison."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


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
        return self.pvalue < alpha


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
    if column not in df.columns:
        raise KeyError(column)
    counts = df.groupby(column, observed=True).size()
    order = sorted(counts.index, key=lambda key: (-int(counts[key]), str(key)))
    return counts.loc[order].astype("int64").rename("requests")


def resolution_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize resolution hours per category with named aggregations.

    Args:
        df: Featured frame.

    Returns:
        One row per category (sorted by median, descending) with columns ``closed``, ``median_hours``,
        ``p90_hours``, and ``outliers``.
    """
    closed = df[df["resolution_hours"].notna()]
    summary = closed.groupby("category").agg(
        closed=("resolution_hours", "size"),
        median_hours=("resolution_hours", "median"),
        p90_hours=("resolution_hours", lambda s: s.quantile(0.9)),
        outliers=("is_outlier", "sum"),
    )
    return summary.astype({"closed": "int64", "outliers": "int64"}).sort_values("median_hours", ascending=False)


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
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    data = np.asarray(pd.Series(values).dropna(), dtype=float)
    if data.size == 0:
        raise ValueError("no observations")
    rng = np.random.default_rng(seed)
    samples = rng.choice(data, size=(n_boot, data.size), replace=True)
    medians = np.median(samples, axis=1)
    tail = (1 - confidence) / 2 * 100
    low, high = np.percentile(medians, [tail, 100 - tail])
    return MedianEstimate(float(np.median(data)), float(low), float(high), confidence, int(data.size))


def weekly_trend(df: pd.DataFrame, window: int = 4) -> pd.DataFrame:
    """Count requests per week (weeks start on Monday) with a trailing rolling mean.

    Args:
        df: Featured frame.
        window: Rolling window in weeks; the first ``window - 1`` weeks average what is available.

    Returns:
        A frame indexed by week start with integer column ``requests`` and float column ``rolling_mean``.
    """
    counts = df.set_index("created_at").resample("W-MON", label="left", closed="left").size().astype("int64")
    counts.index.name = "week"
    return pd.DataFrame({"requests": counts, "rolling_mean": counts.rolling(window, min_periods=1).mean()})


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
    a = df.loc[df["borough"] == borough_a, "resolution_hours"].dropna().to_numpy(dtype=float)
    b = df.loc[df["borough"] == borough_b, "resolution_hours"].dropna().to_numpy(dtype=float)
    if a.size < 2 or b.size < 2:
        raise ValueError(f"need at least two closed requests in each borough (got {a.size} and {b.size})")
    result = stats.mannwhitneyu(a, b, alternative="two-sided")
    return BoroughComparison(
        borough_a=borough_a,
        borough_b=borough_b,
        n_a=int(a.size),
        n_b=int(b.size),
        median_a=float(np.median(a)),
        median_b=float(np.median(b)),
        statistic=float(result.statistic),
        pvalue=float(result.pvalue),
    )
