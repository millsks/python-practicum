"""ISBN normalization and check-digit validation."""

# The imports below are the ones your implementation will need.
# ruff: noqa: F401

from library.errors import InvalidISBNError


def normalize_isbn(raw: str) -> str:
    """Strip hyphens and spaces and upper-case a trailing ``x``.

    Args:
        raw: An ISBN as typed by a person, for example ``"0-306-40615-2"``.

    Returns:
        The ISBN with separators removed, for example ``"0306406152"``.
    """
    # TODO: Remove '-' and ' ', strip, and upper-case (so a trailing 'x' becomes 'X').
    raise NotImplementedError


def is_valid_isbn10(isbn: str) -> bool:
    """Check an ISBN-10 check digit.

    The weighted sum ``10*d1 + 9*d2 + ... + 1*d10`` must be divisible by 11. The last character may be ``X``
    (meaning 10).

    Args:
        isbn: A normalized ten-character ISBN.

    Returns:
        True when the length, characters, and check digit are all valid.
    """
    # TODO: Check length 10, digits in the first nine places, digit or 'X' last; weights 10..1; sum % 11 == 0.
    raise NotImplementedError


def is_valid_isbn13(isbn: str) -> bool:
    """Check an ISBN-13 check digit.

    Digits are weighted alternately 1 and 3; the total must be divisible by 10.

    Args:
        isbn: A normalized thirteen-digit ISBN.

    Returns:
        True when the length, characters, and check digit are all valid.
    """
    # TODO: Check 13 digits; weights alternate 1, 3, 1, 3...; sum % 10 == 0.
    raise NotImplementedError


def isbn10_to_isbn13(isbn10: str) -> str:
    """Convert a valid ISBN-10 to its ISBN-13 form with the ``978`` prefix.

    Args:
        isbn10: A normalized, valid ISBN-10.

    Returns:
        The equivalent ISBN-13.

    Raises:
        InvalidISBNError: If ``isbn10`` is not a valid ISBN-10.
    """
    # TODO: Raise InvalidISBNError if invalid; prefix '978' to the first nine digits; recompute the check digit.
    raise NotImplementedError


def validate_isbn(raw: str) -> str:
    """Validate an ISBN and return it in canonical ISBN-13 form.

    Args:
        raw: An ISBN-10 or ISBN-13, with or without hyphens and spaces.

    Returns:
        The canonical thirteen-digit ISBN.

    Raises:
        InvalidISBNError: If ``raw`` is neither a valid ISBN-10 nor a valid ISBN-13.
    """
    # TODO: Normalize, accept a valid ISBN-13 as-is, convert a valid ISBN-10, otherwise raise InvalidISBNError.
    raise NotImplementedError
