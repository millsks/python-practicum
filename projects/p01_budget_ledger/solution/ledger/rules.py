"""Load categorization rules and budgets, and assign categories to transactions."""

import json
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ledger.errors import LedgerError
from ledger.models import UNCATEGORIZED, Config, Rule, Transaction


def _read_mapping(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".toml":
            with path.open("rb") as handle:
                data: object = tomllib.load(handle)
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            raise LedgerError(f"{path.name}: rules file must be .toml or .json")
    except OSError as exc:
        raise LedgerError(f"cannot read {path}: {exc.strerror or exc}") from exc
    except (tomllib.TOMLDecodeError, json.JSONDecodeError) as exc:
        raise LedgerError(f"{path.name}: invalid {suffix[1:].upper()}: {exc}") from exc
    if not isinstance(data, dict):
        raise LedgerError(f"{path.name}: top level must be a table/object")
    return data


def _parse_rules(raw: object, name: str) -> list[Rule]:
    if not isinstance(raw, Mapping):
        raise LedgerError(f"{name}: 'rules' must map category names to keyword lists")
    rules: list[Rule] = []
    for category, keywords in raw.items():
        if not isinstance(keywords, list) or not all(isinstance(k, str) and k.strip() for k in keywords):
            raise LedgerError(f"{name}: rules.{category} must be a list of non-empty strings")
        rules.append(Rule(str(category), tuple(k.strip().casefold() for k in keywords)))
    return rules


def _parse_budgets(raw: object, name: str) -> dict[str, Decimal]:
    if not isinstance(raw, Mapping):
        raise LedgerError(f"{name}: 'budgets' must map category names to numbers")
    budgets: dict[str, Decimal] = {}
    for category, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, int | float | str):
            raise LedgerError(f"{name}: budgets.{category} must be a number")
        try:
            limit = Decimal(str(value))
        except InvalidOperation as exc:
            raise LedgerError(f"{name}: budgets.{category} must be a number") from exc
        if not limit.is_finite() or limit < 0:
            raise LedgerError(f"{name}: budgets.{category} must be zero or more")
        budgets[str(category)] = limit
    return budgets


def load_config(path: Path) -> Config:
    """Load rules and budgets from a TOML or JSON file.

    The file has two optional sections. ``rules`` maps a category to keywords, checked in file order. ``budgets``
    maps a category to its monthly limit::

        [rules]
        groceries = ["whole foods", "trader joe"]

        [budgets]
        groceries = 400

    Args:
        path: A ``.toml`` or ``.json`` file.

    Returns:
        The parsed configuration.

    Raises:
        LedgerError: If the file is unreadable, has the wrong extension, or has invalid content.
    """
    data = _read_mapping(path)
    return Config(
        rules=_parse_rules(data.get("rules", {}), path.name),
        budgets=_parse_budgets(data.get("budgets", {}), path.name),
    )


def categorize(description: str, rules: Iterable[Rule]) -> str:
    """Return the category of the first rule matching ``description``.

    Args:
        description: Transaction description.
        rules: Rules in priority order.

    Returns:
        The matched category, or ``"uncategorized"`` when nothing matches.
    """
    for rule in rules:
        if rule.matches(description):
            return rule.category
    return UNCATEGORIZED


def categorize_all(transactions: Iterable[Transaction], rules: Iterable[Rule]) -> list[Transaction]:
    """Return copies of ``transactions`` with their category set by ``rules``.

    Args:
        transactions: Transactions to categorize; they are not modified.
        rules: Rules in priority order.

    Returns:
        New transactions in the same order.
    """
    rule_list = list(rules)
    return [replace(t, category=categorize(t.description, rule_list)) for t in transactions]
