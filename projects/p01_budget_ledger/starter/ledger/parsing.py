"""Read bank-export CSV files into :class:`~ledger.models.Transaction` records.

Milestone 1. Run ``pixi run grade p01`` and start with ``tests/test_ledger_parsing.py``.
"""

import csv  # noqa: F401  (you will need it)
from collections.abc import Iterable, Mapping
from datetime import date, datetime  # noqa: F401
from decimal import Decimal, InvalidOperation  # noqa: F401
from pathlib import Path

from ledger.errors import LedgerError  # noqa: F401
from ledger.models import Transaction

REQUIRED_COLUMNS = ("date", "description", "amount")
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y")


def parse_amount(text: str) -> Decimal:
    """Parse a money amount as exported by a bank.

    Accepts an optional ``$`` sign, thousands separators, a leading minus sign, and accounting-style parentheses
    for negative numbers, for example ``"-1,234.50"``, ``"$12"``, or ``"(9.99)"``.

    Args:
        text: The raw cell text.

    Returns:
        The amount as an exact ``Decimal``.

    Raises:
        LedgerError: If the text is empty or not a finite number.
    """
    # TODO: strip whitespace, remove "," and "$".
    # TODO: "(9.99)" means -9.99: detect the parentheses and remember to negate.
    # TODO: Decimal("abc") raises InvalidOperation; convert it to LedgerError with `raise ... from exc`.
    # TODO: Decimal("nan") and Decimal("inf") parse but are not money: check value.is_finite().
    raise NotImplementedError


def parse_date(text: str) -> date:
    """Parse a date in ISO ``YYYY-MM-DD`` or US ``MM/DD/YYYY`` form.

    Args:
        text: The raw cell text.

    Returns:
        The parsed date.

    Raises:
        LedgerError: If the text matches none of :data:`DATE_FORMATS`.
    """
    # TODO: try each format in DATE_FORMATS with datetime.strptime(text, fmt).date().
    # TODO: strptime raises ValueError on a mismatch; try the next format, and raise LedgerError if none work.
    raise NotImplementedError


def parse_row(row: Mapping[str, str | None], *, source: str = "", line: int = 0) -> Transaction:
    """Turn one CSV row (with lower-case keys) into a transaction.

    Args:
        row: Mapping from lower-case column name to cell text; ``None`` marks a missing cell.
        source: File name used in error messages.
        line: Line number used in error messages.

    Returns:
        The parsed transaction, not yet categorized.

    Raises:
        LedgerError: If a required cell is missing or invalid; the message starts with ``source:line:``.
    """
    # TODO: csv.DictReader fills missing cells with None. Treat None as an error.
    # TODO: an empty (or all-space) description is an error.
    # TODO: wrap the work in try/except LedgerError and re-raise with f"{source}:{line}: {exc}" so the user
    #       learns exactly where the bad row is.
    raise NotImplementedError


def read_transactions(path: Path) -> list[Transaction]:
    """Read every transaction from one CSV file.

    The file needs a header row containing ``Date``, ``Description``, and ``Amount`` (any case, any order; extra
    columns are ignored). A UTF-8 byte-order mark, which many banks add, is handled.

    Args:
        path: CSV file to read.

    Returns:
        Transactions in file order.

    Raises:
        LedgerError: If the file cannot be read, lacks required columns, or contains a malformed row.
    """
    # TODO: open with encoding="utf-8-sig" (strips a BOM) and newline="" (required by the csv module).
    # TODO: reader = csv.DictReader(handle); reader.fieldnames is None for an empty file.
    # TODO: normalize headers: reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    # TODO: report missing REQUIRED_COLUMNS by name.
    # TODO: reader.line_num is the current physical line number: pass it to parse_row.
    # TODO: turn OSError (missing file) into LedgerError.
    raise NotImplementedError


def read_many(paths: Iterable[Path]) -> list[Transaction]:
    """Read and concatenate transactions from several CSV files.

    Args:
        paths: CSV files, read in the given order.

    Returns:
        All transactions, file by file.

    Raises:
        LedgerError: If any file fails to parse.
    """
    raise NotImplementedError
