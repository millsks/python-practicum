"""Milestone 5: the command-line interface."""

import json
from pathlib import Path

import pytest
from ledger.cli import main

CSV_JAN = """Date,Description,Amount
2026-01-02,WHOLE FOODS #123,-250.00
2026-01-02,WHOLE FOODS #123,-250.00
2026-01-05,Pizza Palace,-30.00
2026-01-15,Payroll,2000.00
"""
RULES = """
[rules]
groceries = ["whole foods"]
dining = ["pizza"]
income = ["payroll"]

[budgets]
groceries = 300
dining = 100
"""


@pytest.fixture
def files(tmp_path: Path) -> tuple[Path, Path]:
    csv_path = tmp_path / "jan.csv"
    csv_path.write_text(CSV_JAN, encoding="utf-8")
    rules_path = tmp_path / "rules.toml"
    rules_path.write_text(RULES, encoding="utf-8")
    return csv_path, rules_path


def test_summary(files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    csv_path, rules = files
    assert main(["summary", str(csv_path), "--rules", str(rules)]) == 0, "summary should exit 0"
    out = capsys.readouterr().out
    assert "2026-01" in out, "summary prints the month"
    assert "groceries" in out and "-500.00" in out, "summary prints category totals"


def test_summary_without_rules_is_uncategorized(files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["summary", str(files[0])]) == 0, "--rules is optional for summary"
    assert "uncategorized" in capsys.readouterr().out, "without rules everything is uncategorized"


def test_summary_unknown_month(files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["summary", str(files[0]), "--month", "2030-01"]) == 1, "an empty month is a data error"
    assert "error" in capsys.readouterr().err, "errors go to stderr"


def test_duplicates(files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["duplicates", str(files[0])]) == 0, "duplicates should exit 0"
    out = capsys.readouterr().out
    assert "1 duplicate group" in out, "the repeated Whole Foods row is reported"
    assert "jan.csv:2" in out and "jan.csv:3" in out, "duplicates list file:line locations"


def test_budget_over_exits_3(files: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    csv_path, rules = files
    assert main(["budget", str(csv_path), "--rules", str(rules)]) == 3, "overruns exit with status 3"
    out = capsys.readouterr().out
    assert "groceries" in out and "dining" not in out, "only over-budget categories are printed"


def test_budget_within_exits_0(tmp_path: Path, files: tuple[Path, Path]) -> None:
    generous = tmp_path / "generous.json"
    generous.write_text(json.dumps({"rules": {"groceries": ["whole foods"]}, "budgets": {"groceries": 1000}}))
    assert main(["budget", str(files[0]), "--rules", str(generous)]) == 0, "no overruns means exit 0"


def test_budget_requires_rules(files: tuple[Path, Path]) -> None:
    assert main(["budget", str(files[0])]) == 1, "budget without --rules is a data error"


def test_export_json(tmp_path: Path, files: tuple[Path, Path]) -> None:
    csv_path, rules = files
    out = tmp_path / "out" / "report.json"
    assert main(["export", str(csv_path), "--rules", str(rules), "--out", str(out)]) == 0, "export exits 0"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["transactions"] == 4, "the report counts every row"
    assert data["months"]["2026-01"]["groceries"] == "-500.00", "the report holds category totals"


def test_malformed_csv_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("Date,Description,Amount\n2026-01-01,Thing,lots\n", encoding="utf-8")
    assert main(["summary", str(bad)]) == 1, "a malformed row is a data error"
    assert "bad.csv:2" in capsys.readouterr().err, "the error names the file and line"


def test_missing_file_exits_1(tmp_path: Path) -> None:
    assert main(["summary", str(tmp_path / "nope.csv")]) == 1, "a missing file is a data error"


@pytest.mark.parametrize("argv", [[], ["bogus"], ["summary"], ["export", "x.csv"]])
def test_usage_errors_exit_2(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(argv) == 2, f"bad arguments {argv} should exit 2"
    assert "usage" in capsys.readouterr().err, "argparse prints usage on errors"
