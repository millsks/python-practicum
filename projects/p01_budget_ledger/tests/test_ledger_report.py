"""Milestone 4: building and exporting reports."""

import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from ledger.errors import LedgerError
from ledger.models import Transaction
from ledger.report import build_report, export_report

ROWS = [
    Transaction(date(2026, 1, 3), "Whole Foods", Decimal("-50.00"), "groceries", "a.csv", 2),
    Transaction(date(2026, 1, 3), "Whole Foods", Decimal("-50.00"), "groceries", "b.csv", 2),
    Transaction(date(2026, 1, 9), "Payroll", Decimal("1000.00"), "income", "a.csv", 3),
]
BUDGETS = {"groceries": Decimal("80")}


def test_build_report_structure() -> None:
    report = build_report(ROWS, BUDGETS)
    assert report["transactions"] == 3, "report should count transactions"
    assert report["months"] == {"2026-01": {"groceries": Decimal("-100.00"), "income": Decimal("1000.00")}}
    assert report["overruns"] == [
        {
            "month": "2026-01",
            "category": "groceries",
            "limit": Decimal("80"),
            "spent": Decimal("100.00"),
            "over": Decimal("20.00"),
        }
    ], "the groceries overrun should be listed"
    assert len(report["duplicates"]) == 1, "the repeated Whole Foods charge is one duplicate group"
    assert {d["source"] for d in report["duplicates"][0]} == {"a.csv", "b.csv"}, "duplicates name their files"


def test_export_json_round_trip(tmp_path: Path) -> None:
    out = export_report(ROWS, BUDGETS, tmp_path / "reports" / "jan.json")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["months"]["2026-01"]["groceries"] == "-100.00", "money is written as exact strings"
    assert data["duplicates"][0][0]["date"] == "2026-01-03", "dates are written in ISO format"
    assert data["overruns"][0]["over"] == "20.00", "overrun amounts are strings too"


def test_export_csv(tmp_path: Path) -> None:
    out = export_report(ROWS, BUDGETS, tmp_path / "summary.csv")
    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {"month": "2026-01", "category": "groceries", "total": "-100.00"},
        {"month": "2026-01", "category": "income", "total": "1000.00"},
    ], "CSV export has one month,category,total row per summary cell"


def test_export_rejects_unknown_format(tmp_path: Path) -> None:
    with pytest.raises(LedgerError):
        export_report(ROWS, BUDGETS, tmp_path / "report.xlsx")
