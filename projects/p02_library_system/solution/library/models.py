"""Domain records: books, copies, members, and loans."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum, StrEnum
from typing import Self

from library.isbn import validate_isbn

FINE_PER_DAY_CENTS = 25
MAX_FINE_PER_LOAN_CENTS = 1000
FINE_BLOCK_THRESHOLD_CENTS = 500


class MemberTier(Enum):
    """Membership tiers, each with its own loan limit and loan period.

    Each member's value is a ``(label, loan_limit, loan_days)`` tuple.
    """

    CHILD = ("child", 3, 14)
    STANDARD = ("standard", 5, 21)
    PREMIUM = ("premium", 10, 28)

    def __init__(self, label: str, loan_limit: int, loan_days: int) -> None:
        """Unpack the tuple value into named attributes."""
        self.label = label
        self.loan_limit = loan_limit
        self.loan_days = loan_days

    @classmethod
    def from_label(cls, label: str) -> Self:
        """Look up a tier by its label.

        Args:
            label: A label such as ``"standard"`` (case-insensitive).

        Returns:
            The matching tier.

        Raises:
            ValueError: If no tier has that label.
        """
        for tier in cls:
            if tier.label == label.lower():
                return tier
        raise ValueError(f"unknown tier {label!r}")


class CopyStatus(StrEnum):
    """Where a physical copy currently is."""

    AVAILABLE = "available"
    ON_LOAN = "on_loan"
    ON_HOLD_SHELF = "on_hold_shelf"


@dataclass(frozen=True, slots=True)
class Book:
    """A title in the catalog. Physical items are :class:`Copy` records.

    Attributes:
        isbn: Canonical ISBN-13; any valid ISBN-10 or hyphenated form is normalized on creation.
        title: The title.
        authors: One or more author names.
        year: Publication year.
    """

    isbn: str
    title: str
    authors: tuple[str, ...]
    year: int

    def __post_init__(self) -> None:
        """Normalize the ISBN and check the other fields."""
        object.__setattr__(self, "isbn", validate_isbn(self.isbn))
        if not self.title.strip():
            raise ValueError("a book needs a title")
        if not self.authors:
            raise ValueError("a book needs at least one author")

    def __str__(self) -> str:
        """Return ``Title by Author (Year)``."""
        return f"{self.title} by {', '.join(self.authors)} ({self.year})"


@dataclass(slots=True)
class Copy:
    """One physical copy of a book.

    Attributes:
        copy_id: Unique barcode such as ``"C0001"``.
        isbn: ISBN of the book this copy belongs to.
        status: Where the copy is.
        reserved_for: Member id the copy is held for while on the hold shelf.
    """

    copy_id: str
    isbn: str
    status: CopyStatus = CopyStatus.AVAILABLE
    reserved_for: str | None = None

    @property
    def is_available(self) -> bool:
        """Whether anyone may borrow the copy right now."""
        return self.status is CopyStatus.AVAILABLE


@dataclass(slots=True)
class Member:
    """A library card holder.

    Attributes:
        member_id: Unique card number.
        name: Display name.
        tier: Membership tier, which sets loan limits.
        email: Address used by notifiers.
        fines_cents: Unpaid fines in cents.
    """

    member_id: str
    name: str
    tier: MemberTier = MemberTier.STANDARD
    email: str = ""
    fines_cents: int = 0

    @property
    def is_blocked(self) -> bool:
        """Whether unpaid fines prevent borrowing."""
        return self.fines_cents >= FINE_BLOCK_THRESHOLD_CENTS


@dataclass(slots=True)
class Loan:
    """A copy lent to a member.

    Attributes:
        loan_id: Unique identifier.
        copy_id: The copy lent out.
        member_id: The borrower.
        borrowed_on: Checkout date.
        due_on: Date the copy must be back.
        returned_on: Return date, or ``None`` while the loan is open.
    """

    loan_id: str
    copy_id: str
    member_id: str
    borrowed_on: date
    due_on: date
    returned_on: date | None = field(default=None)

    @property
    def is_open(self) -> bool:
        """Whether the copy has not been returned yet."""
        return self.returned_on is None

    def days_overdue(self, today: date) -> int:
        """Count days past the due date.

        Args:
            today: The current date; ignored once the loan is returned.

        Returns:
            Days late at return (or as of ``today`` while open); never negative.
        """
        end = self.returned_on or today
        return max(0, (end - self.due_on).days)

    def is_overdue(self, today: date) -> bool:
        """Whether an open loan is past its due date.

        Args:
            today: The current date.

        Returns:
            True for an open loan with at least one day overdue.
        """
        return self.is_open and self.days_overdue(today) > 0

    def fine_cents(self, today: date) -> int:
        """Compute the late fine for this loan.

        Args:
            today: The current date.

        Returns:
            ``FINE_PER_DAY_CENTS`` per day overdue, capped at ``MAX_FINE_PER_LOAN_CENTS``.
        """
        return min(self.days_overdue(today) * FINE_PER_DAY_CENTS, MAX_FINE_PER_LOAN_CENTS)


def due_date(borrowed_on: date, tier: MemberTier) -> date:
    """Compute when a loan is due.

    Args:
        borrowed_on: Checkout date.
        tier: The borrower's tier.

    Returns:
        ``borrowed_on`` plus the tier's loan period.
    """
    return borrowed_on + timedelta(days=tier.loan_days)
