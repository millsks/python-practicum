"""Build a JSON-ready report and export it as JSON or CSV."""

import csv
import json
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from ledger.analysis import check_budgets, find_duplicates, monthly_summary
from ledger.errors import LedgerError
from ledger.models import Transaction


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def build_report(transactions: Sequence[Transaction], budgets: Mapping[str, Decimal]) -> dict[str, Any]:
    """Collect the summary, overruns, and duplicates into one dictionary.

    Args:
        transactions: Categorized transactions.
        budgets: Monthly limit per category.

    Returns:
        A dictionary with keys ``transactions`` (count), ``months``, ``overruns``, and ``duplicates``. Money values
        are ``Decimal`` and dates are ``date``; :func:`export_report` converts them to strings.
    """
    summary = monthly_summary(transactions)
    return {
        "transactions": len(transactions),
        "months": summary,
        "overruns": [
            {"month": o.month, "category": o.category, "limit": o.limit, "spent": o.spent, "over": o.over}
            for o in check_budgets(summary, budgets)
        ],
        "duplicates": [
            [
                {"date": t.date, "description": t.description, "amount": t.amount, "source": t.source, "line": t.line}
                for t in group
            ]
            for group in find_duplicates(transactions)
        ],
    }


def write_json(report: Mapping[str, Any], path: Path) -> None:
    """Write ``report`` as indented JSON, converting ``Decimal`` and ``date`` values to strings.

    Args:
        report: Output of :func:`build_report`.
        path: Destination file.
    """
    path.write_text(json.dumps(report, indent=2, default=_json_default) + "\n", encoding="utf-8")


def write_summary_csv(summary: Mapping[str, Mapping[str, Decimal]], path: Path) -> None:
    """Write a monthly summary as CSV with columns ``month,category,total``.

    Args:
        summary: Output of :func:`~ledger.analysis.monthly_summary`.
        path: Destination file.
    """
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["month", "category", "total"])
        for month, categories in summary.items():
            for category, total in categories.items():
                writer.writerow([month, category, str(total)])


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
    suffix = path.suffix.lower()
    if suffix not in {".json", ".csv"}:
        raise LedgerError(f"unsupported export format {path.suffix!r}; use .json or .csv")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".json":
            write_json(build_report(transactions, budgets), path)
        else:
            write_summary_csv(monthly_summary(transactions), path)
    except OSError as exc:
        raise LedgerError(f"cannot write {path}: {exc.strerror or exc}") from exc
    return path
