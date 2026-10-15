"""Summaries, duplicate detection, and budget checks over categorized transactions."""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import date
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
    totals: defaultdict[str, defaultdict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for t in transactions:
        totals[t.month][t.category] += t.amount
    return {month: dict(sorted(totals[month].items())) for month in sorted(totals)}


def _duplicate_key(t: Transaction) -> tuple[date, Decimal, str]:
    return t.date, t.amount, " ".join(t.description.casefold().split())


def find_duplicates(transactions: Iterable[Transaction]) -> list[list[Transaction]]:
    """Group transactions that look like the same charge imported more than once.

    Two transactions are duplicates when they share a date and amount and their descriptions are equal ignoring
    case and repeated whitespace.

    Args:
        transactions: Transactions to inspect.

    Returns:
        Groups of two or more matching transactions, in order of first appearance.
    """
    groups: dict[tuple[date, Decimal, str], list[Transaction]] = {}
    for t in transactions:
        groups.setdefault(_duplicate_key(t), []).append(t)
    return [group for group in groups.values() if len(group) > 1]


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
    overruns: list[Overrun] = []
    for month in sorted(summary):
        for category in sorted(budgets):
            spent = -summary[month].get(category, Decimal(0))
            if spent > budgets[category]:
                overruns.append(Overrun(month, category, budgets[category], spent))
    return overruns
