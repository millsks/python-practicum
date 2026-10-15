"""Milestone 5: JSON save/load round-trip."""

import json
from datetime import date

import pytest
from library import Book, FixedClock, Library, Member, MemberTier, PersistenceError, load_library, save_library

DUNE = "9780441172719"
HOBBIT = "9780261102217"


def make_busy_library() -> tuple[Library, FixedClock]:
    clock = FixedClock(date(2026, 2, 1))
    lib = Library(clock=clock)
    lib.add_book(Book(DUNE, "Dune", ("Frank Herbert",), 1965), copies=1)
    lib.add_book(Book(HOBBIT, "The Hobbit", ("J. R. R. Tolkien",), 1937), copies=2)
    lib.register_member(Member("M1", "Ada", MemberTier.PREMIUM, "ada@example.org"))
    lib.register_member(Member("M2", "Grace", MemberTier.CHILD))
    lib.register_member(Member("M3", "Linus"))
    late = lib.checkout("M3", HOBBIT)
    lib.checkout("M1", DUNE)
    lib.place_hold("M2", DUNE)
    clock.advance(30)
    lib.return_copy(late.copy_id)
    return lib, clock


def test_save_writes_versioned_json(tmp_path):
    lib, _ = make_busy_library()
    path = tmp_path / "data" / "library.json"
    save_library(lib, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == 1 and len(data["books"]) == 2, "file is JSON with a version and every book"
    assert data["loans"][0]["borrowed_on"] == "2026-02-01", "dates are ISO strings"


def test_round_trip_preserves_state(tmp_path):
    lib, clock = make_busy_library()
    path = tmp_path / "library.json"
    save_library(lib, path)
    loaded = load_library(path, clock=clock)
    assert loaded.books == lib.books
    assert loaded.members == lib.members, "tiers and fines survive"
    assert loaded.loans == lib.loans, "open and closed loans survive with their dates"
    assert loaded.copies == lib.copies, "copy status survives"
    assert loaded.holds == {DUNE: ["M2"]}
    assert loaded.get_member("M3").fines_cents == 225


def test_loaded_library_keeps_working(tmp_path):
    lib, clock = make_busy_library()
    path = tmp_path / "library.json"
    save_library(lib, path)
    loaded = load_library(path, clock=clock)
    loan = loaded.checkout("M1", HOBBIT)
    assert loan.loan_id == "L00003", "new loan ids continue after the saved ones"
    (copy,) = loaded.add_copies(DUNE, 1)
    assert copy.copy_id == "C00004" and copy.reserved_for == "M2"
    assert loaded.search("herbert")[0].isbn == DUNE, "the search index is rebuilt on load"


def test_load_missing_file(tmp_path):
    with pytest.raises(PersistenceError, match="no saved library"):
        load_library(tmp_path / "missing.json")


def test_load_invalid_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(PersistenceError):
        load_library(path)


@pytest.mark.parametrize("payload", ['{"version": 99}', '{"version": 1, "books": []}', "[1, 2]"])
def test_load_rejects_wrong_shape(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(PersistenceError):
        load_library(path)
