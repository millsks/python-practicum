"""Read bank-export CSV files into :class:`~ledger.models.Transaction` records."""

import csv
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledger.errors import LedgerError
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
    cleaned = text.strip().replace(",", "").replace("$", "")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = cleaned[1:-1].strip()
    if not cleaned:
        raise LedgerError("amount is empty")
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise LedgerError(f"invalid amount {text!r}") from exc
    if not value.is_finite():
        raise LedgerError(f"invalid amount {text!r}")
    return -value if negative else value


def parse_date(text: str) -> date:
    """Parse a date in ISO ``YYYY-MM-DD`` or US ``MM/DD/YYYY`` form.

    Args:
        text: The raw cell text.

    Returns:
        The parsed date.

    Raises:
        LedgerError: If the text matches none of :data:`DATE_FORMATS`.
    """
    cleaned = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise LedgerError(f"invalid date {text!r} (expected YYYY-MM-DD or MM/DD/YYYY)")


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
    try:
        cells = {}
        for column in REQUIRED_COLUMNS:
            value = row.get(column)
            if value is None:
                raise LedgerError(f"missing {column!r} value")
            cells[column] = value
        description = cells["description"].strip()
        if not description:
            raise LedgerError("description is empty")
        return Transaction(
            date=parse_date(cells["date"]),
            description=description,
            amount=parse_amount(cells["amount"]),
            source=source,
            line=line,
        )
    except LedgerError as exc:
        raise LedgerError(f"{source}:{line}: {exc}") from exc


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
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise LedgerError(f"{path.name}: file is empty")
            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
            missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
            if missing:
                raise LedgerError(f"{path.name}: missing column(s): {', '.join(missing)}")
            return [parse_row(row, source=path.name, line=reader.line_num) for row in reader]
    except OSError as exc:
        raise LedgerError(f"cannot read {path}: {exc.strerror or exc}") from exc
    except (UnicodeDecodeError, csv.Error) as exc:
        raise LedgerError(f"{path.name}: not a readable UTF-8 CSV file: {exc}") from exc


def read_many(paths: Iterable[Path]) -> list[Transaction]:
    """Read and concatenate transactions from several CSV files.

    Args:
        paths: CSV files, read in the given order.

    Returns:
        All transactions, file by file.

    Raises:
        LedgerError: If any file fails to parse.
    """
    transactions: list[Transaction] = []
    for path in paths:
        transactions.extend(read_transactions(path))
    return transactions
