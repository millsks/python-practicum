"""Milestone 2: catalog, members, checkout, return, limits, fines, and the injectable clock."""

from datetime import date

import pytest
from library import (
    Book,
    CopyStatus,
    DuplicateError,
    FixedClock,
    InMemoryNotifier,
    Library,
    LoanLimitError,
    Member,
    MemberTier,
    NoCopiesAvailableError,
    NotFoundError,
    OutstandingFinesError,
)

HOBBIT = "9780261102217"
SIGNALS = "9780306406157"


def make_library(copies: int = 1) -> tuple[Library, FixedClock, InMemoryNotifier]:
    clock = FixedClock(date(2026, 3, 1))
    notifier = InMemoryNotifier()
    lib = Library(clock=clock, notifier=notifier)
    lib.add_book(Book(HOBBIT, "The Hobbit", ("J. R. R. Tolkien",), 1937), copies=copies)
    lib.add_book(Book(SIGNALS, "Signals and Systems", ("A. Oppenheim",), 1996), copies=copies)
    lib.register_member(Member("M1", "Ada", MemberTier.STANDARD, "ada@example.org"))
    lib.register_member(Member("M2", "Grace", MemberTier.CHILD, "grace@example.org"))
    return lib, clock, notifier


def test_fixed_clock_advances_and_refuses_to_go_back():
    clock = FixedClock(date(2026, 1, 1))
    clock.advance(10)
    assert clock.today() == date(2026, 1, 11)
    with pytest.raises(ValueError):
        clock.advance(-1)


def test_add_book_creates_numbered_copies():
    lib, _, _ = make_library(copies=2)
    copies = lib.copies_of(HOBBIT)
    assert [c.copy_id for c in copies] == ["C00001", "C00002"], "copy ids are sequential and zero-padded"
    assert lib.available_copies(HOBBIT) == 2
    assert len(lib) == 2 and HOBBIT in lib and "0-306-40615-2" in lib, "len/in work and accept any ISBN form"
    assert "garbage" not in lib and 42 not in lib


def test_duplicates_are_rejected():
    lib, _, _ = make_library()
    with pytest.raises(DuplicateError):
        lib.add_book(Book(HOBBIT, "The Hobbit", ("J. R. R. Tolkien",), 1937))
    with pytest.raises(DuplicateError):
        lib.register_member(Member("M1", "Someone"))


def test_lookups_raise_not_found():
    lib, _, _ = make_library()
    with pytest.raises(NotFoundError):
        lib.get_book("9780141439518")
    with pytest.raises(NotFoundError):
        lib.get_member("nobody")
    with pytest.raises(NotFoundError):
        lib.get_copy("C99999")
    assert issubclass(NotFoundError, LookupError), "NotFoundError is a LookupError"


def test_checkout_sets_due_date_from_clock_and_tier():
    lib, _, _ = make_library()
    loan = lib.checkout("M1", HOBBIT)
    assert loan.borrowed_on == date(2026, 3, 1), "checkout uses the injected clock"
    assert loan.due_on == date(2026, 3, 22), "standard members get 21 days"
    assert lib.get_copy(loan.copy_id).status is CopyStatus.ON_LOAN
    assert lib.loans_for("M1") == [loan]


def test_checkout_without_free_copy_fails():
    lib, _, _ = make_library()
    lib.checkout("M1", HOBBIT)
    with pytest.raises(NoCopiesAvailableError):
        lib.checkout("M2", HOBBIT)


def test_loan_limit_is_enforced_per_tier():
    lib, _, _ = make_library(copies=5)
    for _ in range(3):
        lib.checkout("M2", HOBBIT)
    with pytest.raises(LoanLimitError):
        lib.checkout("M2", SIGNALS)
    assert len(lib.loans_for("M2")) == 3, "child members may borrow 3 items"


def test_on_time_return_has_no_fine():
    lib, clock, notifier = make_library()
    loan = lib.checkout("M1", HOBBIT)
    clock.advance(21)
    closed = lib.return_copy(loan.copy_id)
    assert closed.returned_on == date(2026, 3, 22) and not closed.is_open
    assert lib.get_member("M1").fines_cents == 0
    assert lib.available_copies(HOBBIT) == 1, "the copy goes back on the shelf"
    assert len(notifier) == 0, "no notice for an on-time return"


def test_late_return_charges_fine_and_notifies():
    lib, clock, notifier = make_library()
    loan = lib.checkout("M1", HOBBIT)
    clock.advance(25)
    lib.return_copy(loan.copy_id)
    assert lib.get_member("M1").fines_cents == 100, "4 days late at 25 cents per day"
    assert [n.subject for n in notifier.for_member("M1")] == ["Late return fine"]


def test_returning_a_copy_not_on_loan_fails():
    lib, _, _ = make_library()
    with pytest.raises(NotFoundError):
        lib.return_copy("C00001")


def test_fines_block_borrowing_until_paid():
    lib, clock, _ = make_library(copies=2)
    loan = lib.checkout("M1", HOBBIT)
    clock.advance(21 + 30)
    lib.return_copy(loan.copy_id)
    assert lib.get_member("M1").fines_cents == 750
    with pytest.raises(OutstandingFinesError):
        lib.checkout("M1", SIGNALS)
    assert lib.pay_fine("M1", 300) == 450, "pay_fine returns the remaining balance"
    lib.checkout("M1", SIGNALS)


def test_pay_fine_validates_amount():
    lib, _, _ = make_library()
    with pytest.raises(ValueError):
        lib.pay_fine("M1", 1)
    with pytest.raises(ValueError):
        lib.pay_fine("M1", 0)


def test_overdue_loans_and_notices():
    lib, clock, notifier = make_library(copies=2)
    first = lib.checkout("M2", HOBBIT)
    clock.advance(5)
    lib.checkout("M1", HOBBIT)
    clock.advance(10)
    assert lib.overdue_loans() == [first], "child loan (14 days) is overdue; standard (21) is not"
    assert lib.send_overdue_notices() == 1
    assert "was due on 2026-03-15" in notifier.for_member("M2")[0].body
