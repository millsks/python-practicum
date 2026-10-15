"""Milestone 1: parsing bank exports."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from ledger.errors import LedgerError
from ledger.models import Transaction
from ledger.parsing import parse_amount, parse_date, read_many, read_transactions


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("12.50", Decimal("12.50")),
        ("-4.25", Decimal("-4.25")),
        ("$1,234.56", Decimal("1234.56")),
        ("-$7", Decimal("-7")),
        ("(9.99)", Decimal("-9.99")),
        ("  3  ", Decimal("3")),
    ],
)
def test_parse_amount_accepts_bank_formats(text: str, expected: Decimal) -> None:
    assert parse_amount(text) == expected, f"parse_amount({text!r}) should be {expected}"


def test_parse_amount_returns_decimal() -> None:
    assert isinstance(parse_amount("0.10"), Decimal), "money must be Decimal, not float"


@pytest.mark.parametrize("text", ["", "abc", "12.3.4", "nan", "inf"])
def test_parse_amount_rejects_garbage(text: str) -> None:
    with pytest.raises(LedgerError):
        parse_amount(text)


def test_parse_date_iso_and_us() -> None:
    assert parse_date("2026-01-05") == date(2026, 1, 5), "ISO dates should parse"
    assert parse_date("01/05/2026") == date(2026, 1, 5), "MM/DD/YYYY dates should parse"


@pytest.mark.parametrize("text", ["2026-13-01", "yesterday", "", "05.01.2026"])
def test_parse_date_rejects_invalid(text: str) -> None:
    with pytest.raises(LedgerError):
        parse_date(text)


def test_read_transactions_basic(tmp_path: Path) -> None:
    path = write(
        tmp_path / "jan.csv",
        "Date,Description,Amount\n2026-01-02,Whole Foods Market,-54.20\n2026-01-03,Payroll,2500.00\n",
    )
    rows = read_transactions(path)
    assert rows == [
        Transaction(date(2026, 1, 2), "Whole Foods Market", Decimal("-54.20")),
        Transaction(date(2026, 1, 3), "Payroll", Decimal("2500.00")),
    ], "both rows should be parsed in file order"
    assert rows[0].source == "jan.csv", "source should be the file name"
    assert rows[1].line == 3, "line should be the physical line number in the file"


def test_read_transactions_header_case_order_and_extra_columns(tmp_path: Path) -> None:
    path = write(tmp_path / "b.csv", "amount,Memo, DATE ,description\n-3.00,x,2026-02-01,Coffee\n")
    (t,) = read_transactions(path)
    assert (t.date, t.description, t.amount) == (date(2026, 2, 1), "Coffee", Decimal("-3.00")), (
        "headers should be matched case-insensitively, in any order, ignoring extra columns"
    )


def test_read_transactions_handles_bom_and_quotes(tmp_path: Path) -> None:
    path = tmp_path / "bom.csv"
    path.write_bytes('﻿Date,Description,Amount\n2026-03-01,"Joe\'s Pizza, Downtown","-1,020.00"\n'.encode())
    (t,) = read_transactions(path)
    assert t.description == "Joe's Pizza, Downtown", "quoted commas belong to the field"
    assert t.amount == Decimal("-1020.00"), "a UTF-8 BOM must not break the Date header"


def test_read_transactions_missing_column(tmp_path: Path) -> None:
    path = write(tmp_path / "bad.csv", "Date,Description\n2026-01-01,Thing\n")
    with pytest.raises(LedgerError, match="amount"):
        read_transactions(path)


def test_read_transactions_empty_file(tmp_path: Path) -> None:
    with pytest.raises(LedgerError):
        read_transactions(write(tmp_path / "empty.csv", ""))


@pytest.mark.parametrize(
    "row",
    ["2026-01-01,Thing,abc", "not-a-date,Thing,-1.00", "2026-01-01,Thing", "2026-01-01,   ,-1.00"],
)
def test_malformed_row_raises_with_location(tmp_path: Path, row: str) -> None:
    path = write(tmp_path / "m.csv", f"Date,Description,Amount\n2026-01-01,Ok,-1.00\n{row}\n")
    with pytest.raises(LedgerError, match=r"m\.csv:3"):
        read_transactions(path)


def test_missing_file_is_ledger_error(tmp_path: Path) -> None:
    with pytest.raises(LedgerError):
        read_transactions(tmp_path / "nope.csv")


def test_ledger_error_is_an_exception() -> None:
    assert issubclass(LedgerError, Exception), "LedgerError should subclass Exception"


def test_read_many_concatenates(tmp_path: Path) -> None:
    a = write(tmp_path / "a.csv", "Date,Description,Amount\n2026-01-01,A,-1\n")
    b = write(tmp_path / "b.csv", "Date,Description,Amount\n2026-01-02,B,-2\n2026-01-03,C,-3\n")
    assert [t.description for t in read_many([a, b])] == ["A", "B", "C"], "files should be read in order"
