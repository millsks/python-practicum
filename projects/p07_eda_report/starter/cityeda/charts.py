"""Charts saved straight to PNG.

``matplotlib.figure.Figure`` is used directly instead of ``pyplot``: it needs no GUI, keeps no global state, and
renders with the Agg backend when saved, so it is safe in scripts, tests, and CI.
"""

from pathlib import Path

import pandas as pd

# Okabe-Ito colorblind-safe palette.
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREY = "#999999"


def plot_counts(counts: pd.Series, path: Path, *, title: str) -> Path:
    """Draw a horizontal bar chart of counts, largest at the top.

    Args:
        counts: Counts indexed by label (as returned by ``requests_by``).
        path: Destination PNG (parent folders are created).
        title: Chart title.

    Returns:
        The path written.
    """
    # TODO: from matplotlib.figure import Figure
    #   fig = Figure(figsize=...); ax = fig.subplots(); ax.barh(...); ax.set_title(title)
    #   path.parent.mkdir(parents=True, exist_ok=True); fig.savefig(path, format="png")
    raise NotImplementedError


def plot_weekly_trend(trend: pd.DataFrame, path: Path) -> Path:
    """Draw weekly request counts with the rolling mean on top.

    Args:
        trend: Frame from ``weekly_trend``.
        path: Destination PNG (parent folders are created).

    Returns:
        The path written.
    """
    raise NotImplementedError


def plot_resolution_hist(df: pd.DataFrame, path: Path, *, max_hours: float = 500.0) -> Path:
    """Draw a histogram of resolution hours; values above ``max_hours`` are piled into the last bin.

    Args:
        df: Featured frame.
        path: Destination PNG (parent folders are created).
        max_hours: Right edge of the x-axis.

    Returns:
        The path written.
    """
    raise NotImplementedError
