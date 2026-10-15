"""Render the analysis as a Markdown report."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cityeda.analysis import BoroughComparison, MedianEstimate
from cityeda.clean import CleaningStep


@dataclass(frozen=True, slots=True)
class ReportData:
    """Everything the report needs, already computed.

    Attributes:
        raw_rows: Rows in the raw file.
        clean_rows: Rows after cleaning.
        log: The cleaning log.
        by_category: Counts from ``requests_by(df, "category")``.
        by_borough: Counts from ``requests_by(df, "borough")``.
        median: Overall median resolution time with its bootstrap interval.
        resolution_by_category: Frame from ``resolution_summary``.
        trend: Frame from ``weekly_trend``.
        comparison: The borough comparison.
        charts: Chart paths relative to the report, keyed by name (``"category"``, ``"borough"``, ``"trend"``,
            ``"resolution"``).
    """

    raw_rows: int
    clean_rows: int
    log: Sequence[CleaningStep]
    by_category: pd.Series
    by_borough: pd.Series
    median: MedianEstimate
    resolution_by_category: pd.DataFrame
    trend: pd.DataFrame
    comparison: BoroughComparison
    charts: dict[str, str]


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Format a GitHub-flavored Markdown table.

    Args:
        headers: Column headings.
        rows: Row values; each is converted with ``str``.

    Returns:
        The table, one line per row, without a trailing newline.

    Raises:
        ValueError: If a row's length differs from the number of headers.
    """
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        if len(row) != len(headers):
            raise ValueError(f"row has {len(row)} cells, expected {len(headers)}")
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def _share_rows(counts: pd.Series) -> list[list[object]]:
    total = int(counts.sum())
    return [[label, f"{int(value):,}", f"{value / total:.1%}"] for label, value in counts.items()]


def render_report(data: ReportData) -> str:
    """Render the full report as Markdown.

    Sections: summary, data cleaning (the log as a table), requests by category and by borough, resolution time,
    weekly trend, and the borough comparison with a plain-language interpretation.

    Args:
        data: Computed results.

    Returns:
        Markdown text ending with a single newline.
    """
    m, c = data.median, data.comparison
    busiest = data.trend["requests"].idxmax()
    verdict = (
        f"The difference is statistically significant (p = {c.pvalue:.2g} < 0.05)."
        if c.significant()
        else f"The difference is not statistically significant (p = {c.pvalue:.2g})."
    )
    parts = [
        "# 311 Service Requests: Exploratory Report",
        "## Summary",
        "\n".join(
            [
                f"- Raw rows: {data.raw_rows:,}; rows after cleaning: {data.clean_rows:,}.",
                f"- Most common category: {data.by_category.index[0]} ({int(data.by_category.iloc[0]):,} requests).",
                f"- Median resolution time: {m.median:.1f} hours "
                f"({m.confidence:.0%} bootstrap CI {m.low:.1f} to {m.high:.1f}, n = {m.n:,}).",
                f"- Busiest week: week of {busiest:%Y-%m-%d} ({int(data.trend['requests'].max()):,} requests).",
            ]
        ),
        "## Data cleaning",
        markdown_table(
            ["Rule", "What it does", "Rows affected"], [[s.rule, s.description, s.rows_affected] for s in data.log]
        ),
        "## Requests by category",
        markdown_table(["Category", "Requests", "Share"], _share_rows(data.by_category)),
        f"![Requests by category]({data.charts['category']})",
        "## Requests by borough",
        markdown_table(["Borough", "Requests", "Share"], _share_rows(data.by_borough)),
        f"![Requests by borough]({data.charts['borough']})",
        "## Resolution time",
        f"The median request is resolved in **{m.median:.1f} hours**. Resampling the {m.n:,} closed requests "
        f"2,000 times puts the median between {m.low:.1f} and {m.high:.1f} hours with {m.confidence:.0%} confidence.",
        f"![Resolution time histogram]({data.charts['resolution']})",
        markdown_table(
            ["Category", "Closed", "Median hours", "90th percentile", "Outliers"],
            [
                [name, int(row.closed), f"{row.median_hours:.1f}", f"{row.p90_hours:.1f}", int(row.outliers)]
                for name, row in data.resolution_by_category.iterrows()
            ],
        ),
        "## Weekly trend",
        "Weekly volume (grey) with a 4-week rolling mean (orange).",
        f"![Weekly trend]({data.charts['trend']})",
        f"## {c.borough_a} vs {c.borough_b}",
        markdown_table(
            ["Borough", "Closed requests", "Median hours"],
            [[c.borough_a, f"{c.n_a:,}", f"{c.median_a:.1f}"], [c.borough_b, f"{c.n_b:,}", f"{c.median_b:.1f}"]],
        ),
        f"Mann-Whitney U = {c.statistic:,.0f}. {verdict} A small p-value says a difference this large would be "
        "rare if the two boroughs had the same distribution; it does not say how large or important the gap is.",
    ]
    return "\n\n".join(parts) + "\n"


def write_report(text: str, path: Path) -> Path:
    """Write report text to ``path`` as UTF-8, creating parent directories.

    Args:
        text: Markdown text.
        path: Destination file.

    Returns:
        The path written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
