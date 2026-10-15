"""Feature engineering on cleaned 311 data."""

import pandas as pd

WEEKDAYS: tuple[str, ...] = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def iqr_outliers(values: pd.Series, k: float = 3.0) -> pd.Series:
    """Flag values outside Tukey's fences ``[Q1 - k*IQR, Q3 + k*IQR]``.

    Missing values are never flagged.

    Args:
        values: Numeric series.
        k: Fence multiplier; 1.5 is the classic boxplot rule, 3.0 marks only extreme values.

    Returns:
        A boolean series aligned with ``values``.
    """
    # TODO: q1, q3 = values.quantile([0.25, 0.75]); compare against the fences; NaN compares False.
    raise NotImplementedError


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add analysis columns to a cleaned frame.

    New columns:

    - ``resolution_hours`` (float): hours from ``created_at`` to ``closed_at``; ``NaN`` when not closed.
    - ``weekday`` (ordered categorical, Monday first): day the request was created.
    - ``hour`` (int): hour of day the request was created (0-23).
    - ``week`` (datetime64): the Monday that starts the request's week.
    - ``is_outlier`` (bool): ``resolution_hours`` beyond ``iqr_outliers(k=3.0)`` computed within its own
      category (a 200-hour wait is normal for a street light but extreme for a noise complaint).

    Args:
        df: Frame from ``clean_requests``.

    Returns:
        A new frame with the added columns; ``df`` is unchanged.
    """
    # TODO: timedelta .dt.total_seconds() / 3600; .dt.day_name(); .dt.hour; .dt.normalize() minus .dt.weekday days.
    # TODO: is_outlier: hours.groupby(df["category"]).transform(iqr_outliers).
    raise NotImplementedError
