"""Milestone 1a: ISBN normalization and check digits."""

import pytest
from library.errors import InvalidISBNError, LibraryError
from library.isbn import is_valid_isbn10, is_valid_isbn13, isbn10_to_isbn13, normalize_isbn, validate_isbn


def test_normalize_strips_hyphens_spaces_and_uppercases_x():
    assert normalize_isbn(" 0-8044-2957-x ") == "080442957X", "remove separators and upper-case a trailing x"


@pytest.mark.parametrize("isbn", ["0306406152", "080442957X", "0198526636"])
def test_valid_isbn10(isbn):
    assert is_valid_isbn10(isbn), f"{isbn} has a correct ISBN-10 check digit"


@pytest.mark.parametrize("isbn", ["0306406153", "030640615", "03064061521", "03064X6152", "X306406152"])
def test_invalid_isbn10(isbn):
    assert not is_valid_isbn10(isbn), f"{isbn} must be rejected (bad digit, length, or misplaced X)"


@pytest.mark.parametrize("isbn", ["9780306406157", "9780261102217", "9780141439518"])
def test_valid_isbn13(isbn):
    assert is_valid_isbn13(isbn), f"{isbn} has a correct ISBN-13 check digit"


@pytest.mark.parametrize("isbn", ["9780306406158", "978030640615", "978030640615X"])
def test_invalid_isbn13(isbn):
    assert not is_valid_isbn13(isbn), f"{isbn} must be rejected"


def test_isbn10_to_isbn13_recomputes_check_digit():
    assert isbn10_to_isbn13("0306406152") == "9780306406157", "prefix 978 and recompute the check digit"
    assert isbn10_to_isbn13("080442957X") == "9780804429573", "an X check digit is replaced, not copied"


def test_isbn10_to_isbn13_rejects_invalid_input():
    with pytest.raises(InvalidISBNError):
        isbn10_to_isbn13("0306406153")


def test_validate_isbn_returns_canonical_isbn13():
    assert validate_isbn("0-306-40615-2") == "9780306406157", "ISBN-10 input becomes ISBN-13"
    assert validate_isbn("978-0-306-40615-7") == "9780306406157", "hyphenated ISBN-13 is normalized"


def test_validate_isbn_error_is_a_library_and_value_error():
    with pytest.raises(InvalidISBNError, match="invalid ISBN"):
        validate_isbn("not-an-isbn")
    assert issubclass(InvalidISBNError, LibraryError), "every error derives from LibraryError"
    assert issubclass(InvalidISBNError, ValueError), "InvalidISBNError is also a ValueError"
