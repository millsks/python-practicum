"""Milestone 3: holds (a deque waiting list) and notifications."""

from collections import deque
from datetime import date

import pytest
from library import Book, CopyStatus, FixedClock, HoldError, InMemoryNotifier, Library, Member, NoCopiesAvailableError
from library.notify import Notifier

DUNE = "9780441172719"


def make_library() -> tuple[Library, InMemoryNotifier]:
    notifier = InMemoryNotifier()
    lib = Library(clock=FixedClock(date(2026, 5, 1)), notifier=notifier)
    lib.add_book(Book(DUNE, "Dune", ("Frank Herbert",), 1965))
    for member_id, name in [("M1", "Ada"), ("M2", "Grace"), ("M3", "Linus")]:
        lib.register_member(Member(member_id, name))
    return lib, notifier


def test_in_memory_notifier_satisfies_protocol():
    notifier: Notifier = InMemoryNotifier()
    notifier.send(Member("M9", "Test"), "Hi", "Body")
    assert isinstance(notifier, InMemoryNotifier) and len(notifier) == 1


def test_cannot_hold_a_title_on_the_shelf():
    lib, _ = make_library()
    with pytest.raises(HoldError):
        lib.place_hold("M1", DUNE)


def test_holds_queue_in_order():
    lib, _ = make_library()
    lib.checkout("M1", DUNE)
    assert lib.place_hold("M2", DUNE) == 1, "first in line"
    assert lib.place_hold("M3", DUNE) == 2, "second in line"
    assert lib.holds_for(DUNE) == ["M2", "M3"]
    assert lib.holds == {DUNE: ["M2", "M3"]}


def test_duplicate_and_self_holds_are_rejected():
    lib, _ = make_library()
    lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    with pytest.raises(HoldError):
        lib.place_hold("M2", DUNE)
    with pytest.raises(HoldError):
        lib.place_hold("M1", DUNE)


def test_return_moves_copy_to_hold_shelf_and_notifies_first_in_line():
    lib, notifier = make_library()
    loan = lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    lib.place_hold("M3", DUNE)
    lib.return_copy(loan.copy_id)
    copy = lib.get_copy(loan.copy_id)
    assert copy.status is CopyStatus.ON_HOLD_SHELF and copy.reserved_for == "M2"
    assert [n.subject for n in notifier.for_member("M2")] == ["Hold ready"]
    assert lib.holds_for(DUNE) == ["M3"], "M2 left the queue when the copy was set aside"


def test_reserved_copy_only_goes_to_its_member():
    lib, _ = make_library()
    loan = lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    lib.return_copy(loan.copy_id)
    with pytest.raises(NoCopiesAvailableError):
        lib.checkout("M3", DUNE)
    new_loan = lib.checkout("M2", DUNE)
    assert new_loan.copy_id == loan.copy_id and lib.get_copy(loan.copy_id).reserved_for is None


def test_cancel_hold_in_queue_and_on_shelf():
    lib, notifier = make_library()
    loan = lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    lib.place_hold("M3", DUNE)
    lib.cancel_hold("M3", DUNE)
    assert lib.holds_for(DUNE) == ["M2"]
    lib.return_copy(loan.copy_id)
    lib.cancel_hold("M2", DUNE)
    assert lib.available_copies(DUNE) == 1, "a cancelled shelf hold releases the copy"
    with pytest.raises(HoldError):
        lib.cancel_hold("M2", DUNE)
    assert len(notifier.for_member("M3")) == 0


def test_new_copies_serve_the_queue_first():
    lib, notifier = make_library()
    lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    (copy,) = lib.add_copies(DUNE, 1)
    assert copy.reserved_for == "M2", "a newly added copy goes to the first waiting member"
    assert lib.holds_for(DUNE) == [] and notifier.for_member("M2")


def test_holds_use_a_deque():
    lib, _ = make_library()
    lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    assert isinstance(lib._holds[DUNE], deque), "waiting lists should be deques for O(1) popleft"
