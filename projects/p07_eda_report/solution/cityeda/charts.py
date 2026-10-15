"""Charts saved straight to PNG.

``matplotlib.figure.Figure`` is used directly instead of ``pyplot``: it needs no GUI, keeps no global state, and
renders with the Agg backend when saved, so it is safe in scripts, tests, and CI.
"""

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

# Okabe-Ito colorblind-safe palette.
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREY = "#999999"


def _save(fig: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="png", dpi=110, bbox_inches="tight")
    return path


def plot_counts(counts: pd.Series, path: Path, *, title: str) -> Path:
    """Draw a horizontal bar chart of counts, largest at the top.

    Args:
        counts: Counts indexed by label (as returned by ``requests_by``).
        path: Destination PNG.
        title: Chart title.

    Returns:
        The path written.
    """
    fig = Figure(figsize=(7, 0.45 * len(counts) + 1.2))
    ax = fig.subplots()
    ordered = counts.iloc[::-1]
    ax.barh([str(label) for label in ordered.index], ordered.to_numpy(), color=BLUE)
    ax.set_title(title, loc="left")
    ax.set_xlabel("Requests")
    ax.spines[["top", "right"]].set_visible(False)
    for y, value in enumerate(ordered.to_numpy()):
        ax.annotate(f"{value:,}", (value, y), xytext=(3, 0), textcoords="offset points", va="center", fontsize=8)
    return _save(fig, path)


def plot_weekly_trend(trend: pd.DataFrame, path: Path) -> Path:
    """Draw weekly request counts with the rolling mean on top.

    Args:
        trend: Frame from ``weekly_trend``.
        path: Destination PNG.

    Returns:
        The path written.
    """
    fig = Figure(figsize=(8, 3.5))
    ax = fig.subplots()
    ax.plot(trend.index, trend["requests"], color=GREY, marker="o", markersize=3, linewidth=1, label="Weekly requests")
    ax.plot(trend.index, trend["rolling_mean"], color=ORANGE, linewidth=2.5, label="Rolling mean")
    ax.set_title("Requests per week", loc="left")
    ax.set_ylabel("Requests")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    return _save(fig, path)


def plot_resolution_hist(df: pd.DataFrame, path: Path, *, max_hours: float = 500.0) -> Path:
    """Draw a histogram of resolution hours; values above ``max_hours`` are piled into the last bin.

    Args:
        df: Featured frame.
        path: Destination PNG.
        max_hours: Right edge of the x-axis.

    Returns:
        The path written.
    """
    hours = df["resolution_hours"].dropna()
    median = float(hours.median()) if len(hours) else 0.0
    fig = Figure(figsize=(7, 3.5))
    ax = fig.subplots()
    ax.hist(hours.clip(upper=max_hours), bins=50, range=(0, max_hours), color=BLUE)
    ax.axvline(median, color=ORANGE, linewidth=2)
    ax.annotate(
        f"median {median:.1f} h",
        (median, 1),
        xycoords=("data", "axes fraction"),
        xytext=(5, -12),
        textcoords="offset points",
        color=ORANGE,
    )
    ax.set_title("Time to resolve a request", loc="left")
    ax.set_xlabel(f"Hours (values over {max_hours:.0f} shown in the last bar)")
    ax.set_ylabel("Requests")
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, path)
