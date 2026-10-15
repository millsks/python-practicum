"""Load categorization rules and budgets, and assign categories to transactions.

Milestone 2. Tests: ``tests/test_ledger_rules.py``.
"""

import json  # noqa: F401
import tomllib  # noqa: F401
from collections.abc import Iterable
from dataclasses import replace  # noqa: F401
from decimal import Decimal, InvalidOperation  # noqa: F401
from pathlib import Path

from ledger.errors import LedgerError  # noqa: F401
from ledger.models import UNCATEGORIZED, Config, Rule, Transaction  # noqa: F401


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
    # TODO: choose the parser from path.suffix: tomllib.load needs a file opened in binary mode ("rb");
    #       json.loads takes text. Any other suffix is a LedgerError.
    # TODO: convert OSError, tomllib.TOMLDecodeError, and json.JSONDecodeError into LedgerError.
    # TODO: rules: each value must be a list of non-empty strings; store keywords lower-cased (str.casefold)
    #       as a tuple, keeping the file's order: Rule(category, tuple(...)).
    # TODO: budgets: accept int, float, or numeric str (but not bool, which is a subclass of int!).
    #       Convert with Decimal(str(value)) so 120.50 stays exact; negative limits are errors.
    # TODO: both sections are optional; a missing one means an empty list/dict.
    raise NotImplementedError


def categorize(description: str, rules: Iterable[Rule]) -> str:
    """Return the category of the first rule matching ``description``.

    Args:
        description: Transaction description.
        rules: Rules in priority order.

    Returns:
        The matched category, or ``"uncategorized"`` when nothing matches.
    """
    # TODO: Rule.matches (in models.py) already does the case-insensitive check.
    raise NotImplementedError


def categorize_all(transactions: Iterable[Transaction], rules: Iterable[Rule]) -> list[Transaction]:
    """Return copies of ``transactions`` with their category set by ``rules``.

    Args:
        transactions: Transactions to categorize; they are not modified.
        rules: Rules in priority order.

    Returns:
        New transactions in the same order.
    """
    # TODO: Transaction is frozen, so build new ones: dataclasses.replace(t, category=...).
    # TODO: `rules` may be an iterator you can only loop over once: turn it into a list first.
    raise NotImplementedError
