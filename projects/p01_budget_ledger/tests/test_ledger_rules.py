"""Milestone 2: rules, budgets, and categorization."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from ledger.errors import LedgerError
from ledger.models import Rule, Transaction
from ledger.rules import categorize, categorize_all, load_config

TOML = """
[rules]
groceries = ["Whole Foods", "trader joe"]
dining = ["pizza", "cafe"]
coffee = ["cafe"]

[budgets]
groceries = 400
dining = 120.50
"""


def test_load_config_toml(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_text(TOML, encoding="utf-8")
    config = load_config(path)
    assert [r.category for r in config.rules] == ["groceries", "dining", "coffee"], "rule order must be kept"
    assert config.rules[0].keywords == ("whole foods", "trader joe"), "keywords should be lower-cased"
    assert config.budgets == {"groceries": Decimal("400"), "dining": Decimal("120.50")}, "budgets become Decimal"


def test_load_config_json(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"rules": {"rent": ["landlord"]}, "budgets": {"rent": 1500}}), encoding="utf-8")
    config = load_config(path)
    assert config.rules == [Rule("rent", ("landlord",))], "JSON rules should load like TOML"
    assert config.budgets == {"rent": Decimal("1500")}, "JSON budgets should load"


def test_load_config_sections_optional(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_text("[rules]\nfun = ['cinema']\n", encoding="utf-8")
    assert load_config(path).budgets == {}, "a missing [budgets] section means no budgets"


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("r.toml", "[rules\n"),
        ("r.json", "{not json"),
        ("r.yaml", "rules: {}"),
        ("r.toml", "rules = 5"),
        ("r.toml", "[rules]\nx = 'not a list'\n"),
        ("r.toml", "[budgets]\nx = 'lots'\n"),
        ("r.toml", "[budgets]\nx = -5\n"),
        ("r.toml", "[budgets]\nx = true\n"),
    ],
)
def test_load_config_rejects_bad_files(tmp_path: Path, name: str, text: str) -> None:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    with pytest.raises(LedgerError):
        load_config(path)


def test_load_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LedgerError):
        load_config(tmp_path / "missing.toml")


def test_categorize_first_match_wins_case_insensitive() -> None:
    rules = [Rule("dining", ("cafe",)), Rule("coffee", ("cafe", "espresso"))]
    assert categorize("BLUE CAFE #12", rules) == "dining", "matching ignores case and the first rule wins"
    assert categorize("Espresso Bar", rules) == "coffee", "later rules still match"


def test_categorize_default() -> None:
    assert categorize("Mystery", [Rule("x", ("zzz",))]) == "uncategorized", "no match means 'uncategorized'"
    assert categorize("Anything", []) == "uncategorized", "no rules means 'uncategorized'"


def test_categorize_all_returns_new_objects() -> None:
    original = [Transaction(date(2026, 1, 1), "Pizza Palace", Decimal("-20"))]
    result = categorize_all(original, [Rule("dining", ("pizza",))])
    assert result[0].category == "dining", "the category should be assigned"
    assert original[0].category == "uncategorized", "the input transactions must not change"
