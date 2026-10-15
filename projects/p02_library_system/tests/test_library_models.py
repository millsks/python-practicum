"""Milestone 1b: Book, Copy, Member, MemberTier, and Loan records."""

import dataclasses
from datetime import date

import pytest
from library.errors import InvalidISBNError
from library.models import Book, Copy, CopyStatus, Loan, Member, MemberTier, due_date


def test_book_normalizes_isbn_on_creation():
    book = Book("0-306-40615-2", "Signals", ("A. Author",), 1999)
    assert book.isbn == "9780306406157", "Book stores the canonical ISBN-13"


def test_book_rejects_bad_isbn_title_and_authors():
    with pytest.raises(InvalidISBNError):
        Book("123", "Title", ("Someone",), 2000)
    with pytest.raises(ValueError):
        Book("9780306406157", "   ", ("Someone",), 2000)
    with pytest.raises(ValueError):
        Book("9780306406157", "Title", (), 2000)


def test_book_is_frozen_and_hashable():
    book = Book("9780261102217", "The Hobbit", ("J. R. R. Tolkien",), 1937)
    with pytest.raises(dataclasses.FrozenInstanceError):
        book.title = "Other"  # type: ignore[misc]
    assert len({book, Book("9780261102217", "The Hobbit", ("J. R. R. Tolkien",), 1937)}) == 1, "equal books hash equal"


def test_book_str():
    book = Book("9780261102217", "The Hobbit", ("J. R. R. Tolkien",), 1937)
    assert str(book) == "The Hobbit by J. R. R. Tolkien (1937)", "str() reads Title by Author (Year)"


def test_member_tiers_have_limits_and_periods():
    assert (MemberTier.CHILD.loan_limit, MemberTier.CHILD.loan_days) == (3, 14)
    assert (MemberTier.STANDARD.loan_limit, MemberTier.STANDARD.loan_days) == (5, 21)
    assert (MemberTier.PREMIUM.loan_limit, MemberTier.PREMIUM.loan_days) == (10, 28)


def test_member_tier_from_label():
    assert MemberTier.from_label("Premium") is MemberTier.PREMIUM, "labels are case-insensitive"
    with pytest.raises(ValueError):
        MemberTier.from_label("gold")


def test_member_defaults_and_blocking():
    member = Member("M1", "Ada")
    assert member.tier is MemberTier.STANDARD and member.fines_cents == 0, "defaults: standard tier, no fines"
    assert not member.is_blocked
    member.fines_cents = 500
    assert member.is_blocked, "500 cents or more of fines blocks borrowing"


def test_copy_starts_available():
    copy = Copy("C00001", "9780261102217")
    assert copy.status is CopyStatus.AVAILABLE and copy.is_available and copy.reserved_for is None


def test_due_date_uses_tier_period():
    assert due_date(date(2026, 1, 1), MemberTier.CHILD) == date(2026, 1, 15)
    assert due_date(date(2026, 1, 1), MemberTier.PREMIUM) == date(2026, 1, 29)


def test_loan_overdue_and_fine_math():
    loan = Loan("L1", "C1", "M1", date(2026, 1, 1), date(2026, 1, 22))
    assert loan.is_open
    assert not loan.is_overdue(date(2026, 1, 22)), "due today is not overdue"
    assert loan.days_overdue(date(2026, 1, 25)) == 3
    assert loan.fine_cents(date(2026, 1, 25)) == 75, "25 cents per day overdue"
    assert loan.fine_cents(date(2026, 6, 1)) == 1000, "fines are capped at 1000 cents per loan"


def test_returned_loan_stops_accruing():
    loan = Loan("L1", "C1", "M1", date(2026, 1, 1), date(2026, 1, 22), returned_on=date(2026, 1, 24))
    assert not loan.is_open and not loan.is_overdue(date(2026, 3, 1)), "a returned loan is never overdue"
    assert loan.days_overdue(date(2026, 3, 1)) == 2, "lateness is measured at the return date"
