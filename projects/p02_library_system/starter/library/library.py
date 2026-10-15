"""The :class:`Library` service: catalog, members, loans, holds, fines, and search."""

# The imports below are the ones your implementation will need.
# ruff: noqa: F401

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Self

from library.clock import Clock, SystemClock
from library.errors import (
    DuplicateError,
    HoldError,
    LoanLimitError,
    NoCopiesAvailableError,
    NotFoundError,
    OutstandingFinesError,
)
from library.isbn import validate_isbn
from library.models import Book, Copy, CopyStatus, Loan, Member, due_date
from library.notify import InMemoryNotifier, Notifier
from library.search import SearchIndex


class Library:
    """A small library's circulation system.

    Args:
        clock: Source of today's date; defaults to the real calendar.
        notifier: Delivers messages to members; defaults to an :class:`InMemoryNotifier`.
    """

    def __init__(self, *, clock: Clock | None = None, notifier: Notifier | None = None) -> None:
        """Create an empty library."""
        self.clock: Clock = clock if clock is not None else SystemClock()
        self.notifier: Notifier = notifier if notifier is not None else InMemoryNotifier()
        self._books: dict[str, Book] = {}
        self._copies: dict[str, Copy] = {}
        self._members: dict[str, Member] = {}
        self._loans: dict[str, Loan] = {}
        self._holds: dict[str, deque[str]] = {}
        self._index = SearchIndex()
        self._next_copy = 1
        self._next_loan = 1

    @classmethod
    def from_records(
        cls,
        *,
        books: Iterable[Book],
        copies: Iterable[Copy],
        members: Iterable[Member],
        loans: Iterable[Loan],
        holds: Mapping[str, Iterable[str]],
        clock: Clock | None = None,
        notifier: Notifier | None = None,
    ) -> Self:
        """Rebuild a library from previously saved records.

        Args:
            books: Catalog entries.
            copies: Physical copies, with their current status.
            members: Card holders, with their fines.
            loans: Open and closed loans.
            holds: Waiting lists keyed by ISBN, first in line first.
            clock: Source of today's date.
            notifier: Delivers messages to members.

        Returns:
            A library in the saved state; new ids continue after the highest saved ones.
        """
        # TODO: Create cls(clock=..., notifier=...), fill the dicts, index the books, turn hold lists into deques, and set the id counters past the highest saved ids.
        raise NotImplementedError

    # ---- catalog -------------------------------------------------------------------------------------------

    def add_book(self, book: Book, copies: int = 1) -> list[Copy]:
        """Add a new title with some physical copies.

        Args:
            book: The title to catalog.
            copies: How many copies to create; at least one.

        Returns:
            The new copies.

        Raises:
            DuplicateError: If the ISBN is already cataloged.
            ValueError: If ``copies`` is less than one.
        """
        # TODO: Reject duplicates and copies < 1; store and index the book; delegate to add_copies.
        raise NotImplementedError

    def add_copies(self, isbn: str, count: int) -> list[Copy]:
        """Add more copies of a cataloged title; each one first serves the hold queue.

        Args:
            isbn: ISBN of a cataloged book.
            count: How many copies to add.

        Returns:
            The new copies.
        """
        # TODO: Create Copy(f'C{n:05d}', ...) objects; each new copy goes through _shelve so it serves the hold queue.
        raise NotImplementedError

    def get_book(self, isbn: str) -> Book:
        """Look up a title.

        Args:
            isbn: Any valid form of the ISBN.

        Returns:
            The book.

        Raises:
            NotFoundError: If the book is not cataloged.
        """
        # TODO: Normalize with validate_isbn, look up, and raise NotFoundError (from None) when missing.
        raise NotImplementedError

    def get_copy(self, copy_id: str) -> Copy:
        """Look up a physical copy.

        Args:
            copy_id: The copy's barcode.

        Returns:
            The copy.

        Raises:
            NotFoundError: If no copy has that id.
        """
        # TODO: Look up or raise NotFoundError.
        raise NotImplementedError

    def copies_of(self, isbn: str) -> list[Copy]:
        """Return every copy of a title.

        Args:
            isbn: ISBN of a cataloged book.

        Returns:
            Copies ordered by id.
        """
        # TODO: All copies whose isbn matches the canonical ISBN.
        raise NotImplementedError

    def available_copies(self, isbn: str) -> int:
        """Count copies anyone may borrow now.

        Args:
            isbn: ISBN of a cataloged book.

        Returns:
            The number of available copies.
        """
        # TODO: Count copies where is_available is True.
        raise NotImplementedError

    def search(self, query: str) -> list[Book]:
        """Keyword search over titles and authors.

        Args:
            query: Words that must all appear.

        Returns:
            Matching books sorted by title.
        """
        # TODO: Delegate to the SearchIndex.
        raise NotImplementedError

    @property
    def books(self) -> list[Book]:
        """Every cataloged title."""
        # TODO: Return a list copy so callers cannot mutate internal state.
        raise NotImplementedError

    @property
    def copies(self) -> list[Copy]:
        """Every physical copy."""
        # TODO: Return a list copy.
        raise NotImplementedError

    @property
    def members(self) -> list[Member]:
        """Every registered member."""
        # TODO: Return a list copy.
        raise NotImplementedError

    @property
    def loans(self) -> list[Loan]:
        """Every loan, open and closed."""
        # TODO: Return a list copy.
        raise NotImplementedError

    @property
    def holds(self) -> dict[str, list[str]]:
        """Waiting lists keyed by ISBN, first in line first."""
        # TODO: Return {isbn: list(queue)} for non-empty queues.
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of cataloged titles."""
        # TODO: Number of cataloged titles.
        raise NotImplementedError

    def __contains__(self, isbn: object) -> bool:
        """Return whether an ISBN (in any valid form) is cataloged."""
        # TODO: Non-strings are False; invalid ISBNs are False (catch ValueError); otherwise check the canonical ISBN.
        raise NotImplementedError

    # ---- members -------------------------------------------------------------------------------------------

    def register_member(self, member: Member) -> Member:
        """Register a new card holder.

        Args:
            member: The new member.

        Returns:
            The same member, for chaining.

        Raises:
            DuplicateError: If the member id is taken.
        """
        # TODO: Reject duplicate ids with DuplicateError.
        raise NotImplementedError

    def get_member(self, member_id: str) -> Member:
        """Look up a member.

        Args:
            member_id: Card number.

        Returns:
            The member.

        Raises:
            NotFoundError: If nobody has that card number.
        """
        # TODO: Look up or raise NotFoundError.
        raise NotImplementedError

    def loans_for(self, member_id: str) -> list[Loan]:
        """Return a member's open loans.

        Args:
            member_id: Card number.

        Returns:
            Open loans ordered by due date.
        """
        # TODO: Open loans for the member, sorted by due date (see _by_due).
        raise NotImplementedError

    def pay_fine(self, member_id: str, cents: int) -> int:
        """Record a fine payment.

        Args:
            member_id: Card number.
            cents: Amount paid; positive and no more than the balance.

        Returns:
            The remaining balance in cents.

        Raises:
            ValueError: If the amount is not positive or exceeds the balance.
        """
        # TODO: Validate 0 < cents <= balance; subtract; return the new balance.
        raise NotImplementedError

    # ---- circulation ---------------------------------------------------------------------------------------

    def checkout(self, member_id: str, isbn: str) -> Loan:
        """Lend a copy of a title to a member.

        A copy waiting on the hold shelf for this member is used first; otherwise any available copy.

        Args:
            member_id: Borrower's card number.
            isbn: Title to borrow.

        Returns:
            The new loan, due after the member's tier loan period.

        Raises:
            OutstandingFinesError: If the member owes too much.
            LoanLimitError: If the member is at their tier's limit.
            NoCopiesAvailableError: If no copy is free for this member.
        """
        # TODO: Check, in order: blocked by fines, loan limit, a copy for this member (_copy_for). Then create the Loan with due_date(...) and mark the copy ON_LOAN.
        raise NotImplementedError

    def return_copy(self, copy_id: str) -> Loan:
        """Check a copy back in, charge any late fine, and serve the hold queue.

        Args:
            copy_id: Barcode of the returned copy.

        Returns:
            The closed loan.

        Raises:
            NotFoundError: If the copy has no open loan.
        """
        # TODO: Find the open loan for the copy; set returned_on from the clock; add any fine to the member and notify; then _shelve the copy.
        raise NotImplementedError

    def overdue_loans(self) -> list[Loan]:
        """Return every open loan past its due date.

        Returns:
            Overdue loans, most overdue first.
        """
        # TODO: Open loans that are overdue today, sorted by due date.
        raise NotImplementedError

    def send_overdue_notices(self) -> int:
        """Notify every member with an overdue loan, once per loan.

        Returns:
            How many notices were sent.
        """
        # TODO: Send one 'Overdue' notice per overdue loan mentioning the title and due date; return the count.
        raise NotImplementedError

    # ---- holds ---------------------------------------------------------------------------------------------

    def place_hold(self, member_id: str, isbn: str) -> int:
        """Join the waiting list for a title with no free copies.

        Args:
            member_id: Card number.
            isbn: Title to wait for.

        Returns:
            The member's 1-based position in the queue.

        Raises:
            HoldError: If a copy is available, the member already has a hold, or already has the title on loan.
        """
        # TODO: Refuse when a copy is available, when the member is already queued or has a copy reserved, or has the title on loan. Append to a deque; return the 1-based position.
        raise NotImplementedError

    def cancel_hold(self, member_id: str, isbn: str) -> None:
        """Leave a waiting list, releasing any copy held on the shelf for the member.

        Args:
            member_id: Card number.
            isbn: Title of the hold.

        Raises:
            HoldError: If the member has no hold on the title.
        """
        # TODO: Remove from the queue; or release a copy reserved on the shelf via _shelve; otherwise raise HoldError.
        raise NotImplementedError

    def holds_for(self, isbn: str) -> list[str]:
        """Return the waiting list for a title.

        Args:
            isbn: Title to inspect.

        Returns:
            Member ids, first in line first.
        """
        # TODO: Return the waiting list as a list.
        raise NotImplementedError

    # ---- helpers -------------------------------------------------------------------------------------------

    def _copy_for(self, member_id: str, isbn: str) -> Copy | None:
        # TODO: Prefer a copy reserved for this member, else any available copy, else None.
        raise NotImplementedError

    def _shelve(self, copy: Copy) -> None:
        """Put a copy back: onto the hold shelf for the next member in line, or onto the open shelf."""
        # TODO: If someone is waiting, popleft them, mark the copy ON_HOLD_SHELF reserved for them, and notify 'Hold ready'; else make it AVAILABLE.
        raise NotImplementedError


def _by_due(loan: Loan) -> tuple[str, str]:
    # TODO: Sort key: (due_on ISO string, loan_id).
    raise NotImplementedError
