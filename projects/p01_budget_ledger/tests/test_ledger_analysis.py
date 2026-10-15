"""Milestone 3: monthly summaries, duplicates, and budgets."""

from datetime import date
from decimal import Decimal

from ledger.analysis import check_budgets, find_duplicates, monthly_summary
from ledger.models import Overrun, Transaction


def tx(day: str, desc: str, amount: str, category: str = "uncategorized", line: int = 0) -> Transaction:
    return Transaction(date.fromisoformat(day), desc, Decimal(amount), category, "f.csv", line)


SAMPLE = [
    tx("2026-01-03", "Whole Foods", "-50.00", "groceries"),
    tx("2026-01-20", "Trader Joe", "-30.25", "groceries"),
    tx("2026-01-21", "Pizza", "-15.00", "dining"),
    tx("2026-02-01", "Whole Foods", "-10.00", "groceries"),
    tx("2026-01-31", "Payroll", "2000.00", "income"),
]


def test_monthly_summary_totals() -> None:
    summary = monthly_summary(SAMPLE)
    assert summary == {
        "2026-01": {"dining": Decimal("-15.00"), "groceries": Decimal("-80.25"), "income": Decimal("2000.00")},
        "2026-02": {"groceries": Decimal("-10.00")},
    }, "totals should be grouped by YYYY-MM and category"


def test_monthly_summary_sorted_keys() -> None:
    summary = monthly_summary(list(reversed(SAMPLE)))
    assert list(summary) == ["2026-01", "2026-02"], "months should be sorted"
    assert list(summary["2026-01"]) == ["dining", "groceries", "income"], "categories should be sorted"


def test_monthly_summary_empty() -> None:
    assert monthly_summary([]) == {}, "no transactions means an empty summary"


def test_find_duplicates_normalizes_description() -> None:
    a = tx("2026-01-03", "Whole  Foods", "-50.00", line=2)
    b = tx("2026-01-03", "whole foods", "-50.00", line=9)
    c = tx("2026-01-04", "Whole Foods", "-50.00", line=10)
    groups = find_duplicates([a, c, b])
    assert len(groups) == 1, "only the same-day, same-amount, same-description pair is a duplicate"
    assert [t.line for t in groups[0]] == [2, 9], "the group keeps both transactions in input order"


def test_find_duplicates_amount_must_match() -> None:
    a = tx("2026-01-03", "Cafe", "-5.00")
    b = tx("2026-01-03", "Cafe", "-5.01")
    assert find_duplicates([a, b]) == [], "different amounts are not duplicates"


def test_find_duplicates_triple() -> None:
    same = [tx("2026-01-03", "Cafe", "-5.00", line=n) for n in range(3)]
    assert [len(g) for g in find_duplicates(same)] == [3], "three copies form one group of three"


def test_check_budgets_overrun() -> None:
    budgets = {"groceries": Decimal("75"), "dining": Decimal("20")}
    overruns = check_budgets(monthly_summary(SAMPLE), budgets)
    assert overruns == [Overrun("2026-01", "groceries", Decimal("75"), Decimal("80.25"))], (
        "only January groceries (80.25 > 75) is over budget"
    )
    assert overruns[0].over == Decimal("5.25"), "over should be spent minus limit"


def test_check_budgets_exact_limit_is_fine() -> None:
    budgets = {"dining": Decimal("15.00")}
    assert check_budgets(monthly_summary(SAMPLE), budgets) == [], "spending exactly the limit is not an overrun"


def test_check_budgets_refund_reduces_spending() -> None:
    rows = [tx("2026-03-01", "Shoes", "-100", "shopping"), tx("2026-03-05", "Shoes refund", "40", "shopping")]
    assert check_budgets(monthly_summary(rows), {"shopping": Decimal("70")}) == [], "refunds offset spending"


def test_check_budgets_zero_budget() -> None:
    rows = [tx("2026-03-01", "Arcade", "-1", "fun")]
    (o,) = check_budgets(monthly_summary(rows), {"fun": Decimal("0")})
    assert (o.category, o.spent) == ("fun", Decimal("1")), "any spending exceeds a zero budget"
