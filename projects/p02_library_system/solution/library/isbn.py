"""ISBN normalization and check-digit validation."""

from library.errors import InvalidISBNError


def normalize_isbn(raw: str) -> str:
    """Strip hyphens and spaces and upper-case a trailing ``x``.

    Args:
        raw: An ISBN as typed by a person, for example ``"0-306-40615-2"``.

    Returns:
        The ISBN with separators removed, for example ``"0306406152"``.
    """
    return raw.replace("-", "").replace(" ", "").strip().upper()


def is_valid_isbn10(isbn: str) -> bool:
    """Check an ISBN-10 check digit.

    The weighted sum ``10*d1 + 9*d2 + ... + 1*d10`` must be divisible by 11. The last character may be ``X``
    (meaning 10).

    Args:
        isbn: A normalized ten-character ISBN.

    Returns:
        True when the length, characters, and check digit are all valid.
    """
    if len(isbn) != 10 or not isbn[:9].isdigit() or not (isbn[9].isdigit() or isbn[9] == "X"):
        return False
    digits = [int(ch) for ch in isbn[:9]] + [10 if isbn[9] == "X" else int(isbn[9])]
    total = sum(weight * digit for weight, digit in zip(range(10, 0, -1), digits, strict=True))
    return total % 11 == 0


def is_valid_isbn13(isbn: str) -> bool:
    """Check an ISBN-13 check digit.

    Digits are weighted alternately 1 and 3; the total must be divisible by 10.

    Args:
        isbn: A normalized thirteen-digit ISBN.

    Returns:
        True when the length, characters, and check digit are all valid.
    """
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    total = sum((1 if i % 2 == 0 else 3) * int(ch) for i, ch in enumerate(isbn))
    return total % 10 == 0


def isbn10_to_isbn13(isbn10: str) -> str:
    """Convert a valid ISBN-10 to its ISBN-13 form with the ``978`` prefix.

    Args:
        isbn10: A normalized, valid ISBN-10.

    Returns:
        The equivalent ISBN-13.

    Raises:
        InvalidISBNError: If ``isbn10`` is not a valid ISBN-10.
    """
    if not is_valid_isbn10(isbn10):
        raise InvalidISBNError(f"not a valid ISBN-10: {isbn10!r}")
    body = "978" + isbn10[:9]
    total = sum((1 if i % 2 == 0 else 3) * int(ch) for i, ch in enumerate(body))
    return body + str((10 - total % 10) % 10)


def validate_isbn(raw: str) -> str:
    """Validate an ISBN and return it in canonical ISBN-13 form.

    Args:
        raw: An ISBN-10 or ISBN-13, with or without hyphens and spaces.

    Returns:
        The canonical thirteen-digit ISBN.

    Raises:
        InvalidISBNError: If ``raw`` is neither a valid ISBN-10 nor a valid ISBN-13.
    """
    isbn = normalize_isbn(raw)
    if is_valid_isbn13(isbn):
        return isbn
    if is_valid_isbn10(isbn):
        return isbn10_to_isbn13(isbn)
    raise InvalidISBNError(f"invalid ISBN: {raw!r}")
