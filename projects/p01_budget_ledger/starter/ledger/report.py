"""Build a JSON-ready report and export it as JSON or CSV.

Milestone 4. Tests: ``tests/test_ledger_report.py``.
"""

import csv  # noqa: F401
import json  # noqa: F401
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from ledger.models import Transaction


def build_report(transactions: Sequence[Transaction], budgets: Mapping[str, Decimal]) -> dict[str, Any]:
    """Collect the summary, overruns, and duplicates into one dictionary.

    Args:
        transactions: Categorized transactions.
        budgets: Monthly limit per category.

    Returns:
        A dictionary with keys ``transactions`` (count), ``months``, ``overruns``, and ``duplicates``. Money values
        are ``Decimal`` and dates are ``date``; :func:`export_report` converts them to strings.
    """
    # TODO: "months" is monthly_summary(...).
    # TODO: each overrun is a dict with month, category, limit, spent, over.
    # TODO: each duplicate group is a list of dicts with date, description, amount, source, line.
    raise NotImplementedError


def write_json(report: Mapping[str, Any], path: Path) -> None:
    """Write ``report`` as indented JSON, converting ``Decimal`` and ``date`` values to strings.

    Args:
        report: Output of :func:`build_report`.
        path: Destination file.
    """
    # TODO: json.dumps(report, indent=2, default=fn) calls fn for objects JSON can't encode.
    #       Return str(value) for Decimal, value.isoformat() for date, and raise TypeError otherwise.
    raise NotImplementedError


def write_summary_csv(summary: Mapping[str, Mapping[str, Decimal]], path: Path) -> None:
    """Write a monthly summary as CSV with columns ``month,category,total``.

    Args:
        summary: Output of :func:`~ledger.analysis.monthly_summary`.
        path: Destination file.
    """
    # TODO: open with newline="" and use csv.writer; write the header row first.
    raise NotImplementedError


def export_report(transactions: Sequence[Transaction], budgets: Mapping[str, Decimal], path: Path) -> Path:
    """Export a report, choosing the format from the file extension.

    ``.json`` writes the full report from :func:`build_report`; ``.csv`` writes the monthly summary.

    Args:
        transactions: Categorized transactions.
        budgets: Monthly limit per category.
        path: Destination ending in ``.json`` or ``.csv``. Missing parent directories are created.

    Returns:
        The path written.

    Raises:
        LedgerError: If the extension is unsupported or the file cannot be written.
    """
    # TODO: path.parent.mkdir(parents=True, exist_ok=True) before writing.
    raise NotImplementedError
