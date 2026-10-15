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
    # TODO: header line, a |---| separator line, then one line per row.
    raise NotImplementedError


def render_report(data: ReportData) -> str:
    """Render the full report as Markdown.

    Sections: summary, data cleaning (the log as a table), requests by category and by borough, resolution time,
    weekly trend, and the borough comparison with a plain-language interpretation.

    Args:
        data: Computed results.

    Returns:
        Markdown text ending with a single newline.
    """
    # TODO: build a list of Markdown blocks (headings, bullet lists, tables, ![alt](charts/x.png) images)
    #   and join them with blank lines. Interpret the p-value in words.
    raise NotImplementedError


def write_report(text: str, path: Path) -> Path:
    """Write report text to ``path`` as UTF-8, creating parent directories.

    Args:
        text: Markdown text.
        path: Destination file.

    Returns:
        The path written.
    """
    raise NotImplementedError
