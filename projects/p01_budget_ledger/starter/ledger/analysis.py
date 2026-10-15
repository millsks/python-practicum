"""Summaries, duplicate detection, and budget checks over categorized transactions.

Milestone 3. Tests: ``tests/test_ledger_analysis.py``.
"""

from collections import defaultdict  # noqa: F401
from collections.abc import Iterable, Mapping
from decimal import Decimal

from ledger.models import Overrun, Transaction

type Summary = dict[str, dict[str, Decimal]]


def monthly_summary(transactions: Iterable[Transaction]) -> Summary:
    """Total the amounts per month and category.

    Args:
        transactions: Categorized transactions.

    Returns:
        ``{month: {category: total}}`` with months and categories in sorted order. Totals keep their sign, so
        spending categories are negative.
    """
    # TODO: Transaction.month gives "YYYY-MM". Start every total at Decimal(0), never 0.0.
    # TODO: build plain dicts in sorted order at the end (dicts remember insertion order).
    raise NotImplementedError


def find_duplicates(transactions: Iterable[Transaction]) -> list[list[Transaction]]:
    """Group transactions that look like the same charge imported more than once.

    Two transactions are duplicates when they share a date and amount and their descriptions are equal ignoring
    case and repeated whitespace.

    Args:
        transactions: Transactions to inspect.

    Returns:
        Groups of two or more matching transactions, in order of first appearance.
    """
    # TODO: build a key tuple (date, amount, " ".join(description.casefold().split())) and group with
    #       dict.setdefault(key, []).append(t). Keep only groups with more than one transaction.
    raise NotImplementedError


def check_budgets(summary: Mapping[str, Mapping[str, Decimal]], budgets: Mapping[str, Decimal]) -> list[Overrun]:
    """Report every month and category whose spending exceeded its budget.

    Spending is the negated total of a category (refunds reduce it). Spending exactly at the limit is not an
    overrun.

    Args:
        summary: Output of :func:`monthly_summary`.
        budgets: Monthly limit per category.

    Returns:
        Overruns ordered by month, then category.
    """
    # TODO: spent = -summary[month].get(category, Decimal(0)); an overrun is spent > limit (strictly).
    raise NotImplementedError
